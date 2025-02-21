"""
Test reuse lldb-dap adapter across debug sessions.
"""

import dap_server
from lldbsuite.test.decorators import *
from lldbsuite.test.lldbtest import *
from lldbsuite.test import lldbutil
import lldbdap_testcase
import time
import os


class TestDAP_reuseAdpater(lldbdap_testcase.DAPTestCaseBase):
    @skipIfWindows
    def test_basic_reuse(self):
        """
        Test reuse lldb-dap works across debug sessions.
        """
        program = self.getBuildArtifact("a.out")

        # Keep lldb-dap alive for 10 minutes.
        dapKeepAliveTimeInMS = 10 * 1000 * 60 
        self.build_and_launch(program, disconnectAutomatically=False, keepAliveTimeout=dapKeepAliveTimeInMS)

        source = "main.cpp"
        breakpoint1_line = line_number(source, "// breakpoint 1")
        breakpoint_ids = self.set_source_breakpoints(source, [breakpoint1_line])
        self.continue_to_breakpoints(breakpoint_ids)
        self.dap_server.request_disconnect()

        # Second debug session by reusing lldb-dap.
        self.create_debug_adapter(reuseDapServer=True)
        self.launch(program)
        
        breakpoint2_line = line_number(source, "// breakpoint 2")
        breakpoint_ids = self.set_source_breakpoints(source, [breakpoint2_line])
        self.continue_to_breakpoints(breakpoint_ids)
        self.dap_server.request_disconnect()

    @skipIfWindows
    def test_exception_breakopints(self):
        """
        Test reuse lldb-dap works across debug sessions.
        """
        program = self.getBuildArtifact("a.out")

        # Keep lldb-dap alive for 10 minutes.
        dapKeepAliveTimeInMS = 10 * 1000 * 60
        self.build_and_launch(program, disconnectAutomatically=False, keepAliveTimeout=dapKeepAliveTimeInMS)

        response = self.dap_server.request_setExceptionBreakpoints(
            filters=["cpp_throw", "cpp_catch"]
        )
        self.assertTrue(response)
        self.assertTrue(response["success"])
        self.continue_to_exception_breakpoint("C++ Throw")
        self.dap_server.request_disconnect()

        # Second debug session by reusing lldb-dap.
        self.create_debug_adapter(reuseDapServer=True)
        self.launch(program)

        response = self.dap_server.request_setExceptionBreakpoints(
            filters=["cpp_throw", "cpp_catch"],
        )
        self.assertTrue(response)
        self.assertTrue(response["success"])
        self.continue_to_exception_breakpoint("C++ Throw")
        self.dap_server.request_disconnect()
