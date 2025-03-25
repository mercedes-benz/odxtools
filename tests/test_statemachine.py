# SPDX-License-Identifier: MIT
import unittest

from odxtools.loadfile import load_pdx_file
from odxtools.statemachine import StateMachine

odxdb = load_pdx_file("./examples/somersault.pdx")


class TestStateChart(unittest.TestCase):

    def test_state_chart(self) -> None:
        ecu = odxdb.ecu_variants.somersault_lazy

        self.assertEqual(len(ecu.state_charts), 2)
        self.assertEqual(ecu.state_charts[0].semantic, "annoyed")
        self.assertEqual(ecu.state_charts[1].semantic, "angry")

        annoyed_chart = ecu.state_charts[0]
        self.assertEqual(len(annoyed_chart.states), 4)
        self.assertEqual(len(annoyed_chart.state_transitions), 6)
        self.assertEqual(annoyed_chart.start_state.short_name, "in_bed")

    def test_state_machine(self) -> None:
        ecu = odxdb.ecu_variants.somersault_lazy
        annoyed_chart = ecu.state_charts.annoyed_chart
        angry_chart = ecu.state_charts.angry_chart

        fsm_angry = StateMachine(ecu, angry_chart)
        fsm_annoyed = StateMachine(ecu, annoyed_chart)

        # the initial states of the state machines are the start
        # states of their respective chart
        self.assertEqual(fsm_angry.active_state, angry_chart.start_state)
        self.assertEqual(fsm_annoyed.active_state, annoyed_chart.start_state)

        # not giving a bribe will fail with the lazy ECU variant if it
        # is in an angry mood
        service = ecu.services.session_start
        for _ in (executor := fsm_angry.execute(service)):
            # the state machine is not supposed to do anything because
            # the precondition to execute the "session_start"
            # service's request is not fulfilled
            self.assertTrue(False)
        self.assertEqual(fsm_angry.active_state, angry_chart.start_state)
        self.assertEqual(fsm_angry.succeeded, False)

        # explicitly not giving a bribe fails as well
        service = ecu.services.session_start
        for _ in (executor := fsm_angry.execute(service, bribe=0)):
            # the state machine is not supposed to do anything because
            # the precondition to execute the "session_start"
            # service's request is not fulfilled
            self.assertTrue(False)
        self.assertEqual(fsm_angry.active_state, angry_chart.start_state)
        self.assertEqual(fsm_angry.succeeded, False)

        # giving a small bribe will get an angry lazy ECU out of bed
        n = 0
        for raw_request in (executor := fsm_angry.execute(ecu.services.session_start, bribe=1)):
            n += 1
            self.assertEqual(raw_request, b'\x10\x00\x01')
            resp = service.positive_responses.session
            raw_response = resp.encode(coded_request=raw_request, can_do_backward_flips="false")
            executor.send(raw_response)
        self.assertEqual(n, 1)
        self.assertEqual(fsm_angry.active_state, angry_chart.states.on_street)
        self.assertEqual(fsm_angry.succeeded, True)

        # if the ECU is just annoyed, it will get out of bed even if
        # no bribe is given. if the ECU responds that it can to
        # backward flips, it will end up in the park, else it will go
        # to the street.
        service = ecu.services.session_start
        for raw_request in (executor := fsm_annoyed.execute(ecu.services.session_start)):
            self.assertEqual(raw_request, b'\x10\x00\x00')
            resp = service.positive_responses.session
            raw_response = resp.encode(coded_request=raw_request, can_do_backward_flips="false")
            executor.send(raw_response)
        self.assertEqual(fsm_annoyed.active_state, annoyed_chart.states.on_street)
        self.assertEqual(fsm_annoyed.succeeded, True)

        service = ecu.services.session_start
        fsm_annoyed.active_state = annoyed_chart.start_state
        for raw_request in (executor := fsm_annoyed.execute(ecu.services.session_start, bribe=0)):
            self.assertEqual(raw_request, b'\x10\x00\x00')
            resp = service.positive_responses.session
            raw_response = resp.encode(coded_request=raw_request, can_do_backward_flips="true")
            executor.send(raw_response)
        self.assertEqual(fsm_annoyed.active_state, annoyed_chart.states.in_park)
        self.assertEqual(fsm_annoyed.succeeded, True)


if __name__ == "__main__":
    unittest.main()
