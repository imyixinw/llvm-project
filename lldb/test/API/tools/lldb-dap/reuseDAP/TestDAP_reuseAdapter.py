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


class TestDAP_reuseAdapter(lldbdap_testcase.DAPTestCaseBase):
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

    def test_session_id_update_when_reuse(self):
        """
        Test if vscode session id being updated when lldb-dap reused
        """
        # Add set up command to print out the session id, with a unique identifier as prefix
        program = self.getBuildArtifact("a.out")
        postRunCommands = ["script print('Actual_Session_ID: ' + str(os.getenv('VSCODE_DEBUG_SESSION_ID')))"]

        # Keep lldb-dap alive for 10 minutes.
        dapKeepAliveTimeInMS = 10 * 1000 * 60
        self.build_and_launch(
            program,
            vscode_session_id="test_session_id",
            postRunCommands=postRunCommands,
            disconnectAutomatically=False,
            keepAliveTimeout=dapKeepAliveTimeInMS
        )

        # Validate the session id in the inital launch of lldb-dap
        output = self.get_console()
        lines = filter(lambda x: 'Actual_Session_ID' in x, output.splitlines())
        self.assertTrue(
            any("test_session_id" in l for l in lines), "expect session id in console output"
        )
        self.dap_server.request_disconnect()

        # Second debug session by reusing lldb-dap.
        self.create_debug_adapter(reuseDapServer=True)
        self.launch(
            program,
            vscode_session_id="NEW_session_id",
            postRunCommands=postRunCommands
        )

        # Validate the updated session id in the reused lldb-dap
        output = self.get_console()
        lines = filter(lambda x: 'Actual_Session_ID' in x, output.splitlines())
        self.assertTrue(
            any("NEW_session_id" in l for l in lines), "expect new session id in console output"
        )
        self.dap_server.request_disconnect()
