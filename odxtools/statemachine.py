# SPDX-License-Identifier: MIT
from collections.abc import Generator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .exceptions import odxraise
from .odxtypes import ParameterValueDict
from .state import State
from .statechart import StateChart

if TYPE_CHECKING:
    from .diaglayers.diaglayer import DiagLayer
    from .diagservice import DiagService


@dataclass(kw_only=True)
class StateMachine:
    """Objects of this class represent the runtime state of a state chart

    It is used to track which services can be executed at a given time.

    Usage example (using asynchronous communication routines):

    ```python
    ecu = db.ecu_variants.my_ecu_variant
    fsm = StateMachine(ecu, ecu.state_charts.my_state_chart)

    for raw_request in (executor := fsm.execute(ecu.services.my_service,
                                                param1="hello",
                                                param2=123)):
        # send raw request to the ECU (usually using ISO-TP or DoIP), and
        # receive the response
        await send_to_ecu(raw_request)
        while odxtools.is_response_pending(raw_response := await receive_from_ecu()):
            pass

        executor.send(raw_response)

    print(f"Request send: {fsm.succeeded}")
    ```

    Alternatively, more of the glue functionality can be handled by
    the calling code:

    ```python

    ecu = db.ecu_variants.my_ecu_variant
    fsm = StateMachine(ecu, ecu.state_charts.my_state_chart)

    service = ecu.services.my_service
    request_param_values = { "param1": "hello", "param2":123 }
    if any(pcs.applies(fsm, service.request.parameters, **request_param_values)
           for pcs in service.pre_condition_states):

        # send raw request to the ECU (usually using ISO-TP or DoIP), and
        # receive the response
        raw_req = service.request.encode(**request_param_values)
        await send_data_to_ecu(raw_req)
        while odxtools.is_response_pending(raw_resp := await receive_from_ecu()):
            pass

        done = False
        for decoded_resp_msg in ecu.decode_response(raw_resp, raw_req):
            for stransref in service.state_transition_refs:
                if stransref.execute(decoded_resp.parameters, decoded_resp_msg.param_dict):
                   done = True
                   break
            if done:
               break
    else:
        raise RuntimeException(f"Cannot execute request for service {service.short_name}")
    ```

    """

    succeeded: bool

    @property
    def diag_layer(self) -> "DiagLayer":
        return self._diag_layer

    @property
    def state_chart(self) -> StateChart:
        return self._state_chart

    @property
    def active_state(self) -> State:
        return self._active_state

    @active_state.setter
    def active_state(self, value: State) -> None:
        self._active_state = value

    def __init__(self, diag_layer: "DiagLayer", state_chart: StateChart) -> None:
        self.succeeded = True
        self._diag_layer = diag_layer
        self._state_chart = state_chart
        self._active_state = state_chart.start_state

    def execute(self, service: "DiagService", **service_params: Any
               ) -> Generator[bytes, bytes | bytearray | ParameterValueDict, None]:
        """Run a diagnostic service and update the state machine
        depending on the outcome.

        This simplifies error handling, en- and decoding etc.

        Usage example (using asynchronous communication routines):

        ```python
        ecu = db.ecu_variants.my_ecu_variant
        fsm = StateMachine(ecu, ecu.state_charts.my_state_chart)

        for raw_request in (executor := fsm.execute(ecu.services.my_service,
                                                    param1="hello",
                                                    param2=123)):
            # send raw request to the ECU (usually using ISO-TP or DoIP), and
            # receive the response
            await send_to_ecu(raw_request)
            while odxtools.is_response_pending(raw_response := await receive_from_ecu()):
                pass

            executor.send(raw_response)

        print(f"Request send: {fsm.succeeded}")
        ```

        """
        if service.request is None:
            odxraise("Services without requests are not allowed in this context")
            self.succeeded = False
            return

        # the service can be executed if any of the specified
        # precondition states is fulfilled. (TODO: correct?)
        if service.pre_condition_state_refs is not None:
            if not any(
                    x.applies(self, service.request.parameters, service_params)
                    for x in service.pre_condition_state_refs):
                # if all preconditions which are applicable are
                # invalid (i.e., they evaluate to False), we must not
                # execute the service.
                self.succeeded = False
                return

        raw_req = service.request.encode(**service_params)
        # ask the calling code to send the request to the ECU and
        # report back the reply
        raw_resp = yield raw_req

        decoded_req_params = service.request.decode(raw_req)
        for stransref in service.state_transition_refs:
            # check if the state transition applies for the
            # request. Note that the ODX specification is unclear
            # about which kind of parameters are relevant for
            # STATE-TRANSITION-REF
            if stransref.execute(self, service.request.parameters, decoded_req_params):
                self.succeeded = True
                yield b''
                return

        if raw_resp is None:
            raise RuntimeError("The calling code must send back a reply")
        elif isinstance(raw_resp, (bytes, bytearray)):
            for decoded_resp_msg in self.diag_layer.decode_response(raw_resp, raw_req):
                for stransref in service.state_transition_refs:
                    # we only execute the first applicable state
                    # transition: The spec seems to imply a
                    # deterministic state machine and chaining
                    # transistions most likely is not what the user
                    # expects. (The spec seems to be a bit loose on
                    # this front...)
                    if stransref.execute(self, decoded_resp_msg.coding_object.parameters,
                                         decoded_resp_msg.param_dict):
                        self.succeeded = True
                        yield b''
                        return
        else:
            resp_object = service.positive_responses[0]
            for stransref in service.state_transition_refs:
                if stransref.execute(self, resp_object.parameters, raw_resp):
                    self.succeeded = True
                    yield b''
                    return

        self.succeeded = True
        yield b''
        return
