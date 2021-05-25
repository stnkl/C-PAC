"""Override Nipype's LegacyMultiproc's _prerun_check to tell which
Nodes use too many resources."""
from nipype.pipeline.plugins.legacymultiproc import (
    LegacyMultiProcPlugin as LegacyMultiProc, logger)
from CPAC.pipeline.nipype_pipeline_engine import UNDEFINED_SIZE


class LegacyMultiProcPlugin(LegacyMultiProc):
    def __init__(self, plugin_args=None):
        super().__init__(plugin_args)

    def _prerun_check(self, graph):
        """Check if any node exeeds the available resources"""
        tasks_mem_gb = []
        tasks_num_th = []
        overrun_message_mem = None
        overrun_message_th = None
        for node in graph.nodes():
            try:
                node_memory_estimate = node.mem_gb
            except FileNotFoundError:
                node_memory_estimate = node._apply_mem_x(UNDEFINED_SIZE)
            if node_memory_estimate > self.memory_gb:
                tasks_mem_gb.append((node.name, node_memory_estimate))
            if node.n_procs > self.processors:
                tasks_num_th.append((node.name, node.n_procs))

        if tasks_mem_gb:
            overrun_message_mem = '\n'.join([
                f'\t{overrun[0]}: {overrun[1]} GB' for overrun in tasks_mem_gb
            ])
            logger.warning(
                "The following nodes are estimated to exceed the total amount "
                f"of memory available (%0.2fGB): \n{overrun_message_mem}",
                self.memory_gb,
            )

        if tasks_num_th:
            overrun_message_th = '\n'.join([
                f'\t{overrun[0]}: {overrun[1]} threads' for overrun in
                tasks_num_th])
            logger.warning(
                "Some nodes demand for more threads than available (%d): "
                f"\n{overrun_message_th}",
                self.processors,
            )

        if self.raise_insufficient and (tasks_mem_gb or tasks_num_th):
            raise RuntimeError("\n".join([msg for msg in [
                "Insufficient resources available for job:",
                overrun_message_mem, overrun_message_th
            ] if msg is not None]))
