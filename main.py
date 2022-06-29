import os

import odxtools
from logger import get_formatted_logger


def list_public_attributes(obj):
    return [attribute for attribute in dir(obj)
            if not attribute.startswith('_') and
            not callable(getattr(obj, attribute))]


def list_callable_functions(obj):
    return [attribute for attribute in dir(obj)
            if not attribute.startswith('_') and
            callable(getattr(obj, attribute))]


os.environ['LOGGER_LEVEL'] = '20'
logger = get_formatted_logger()

db = odxtools.load_file("/Users/smileprem/Downloads/ODX/Volta/AVAS_V2.0.1.pdx")
print(db.id_lookup['_New_ECU_1_306'])
electronicControlUnits = []
services = []
for ecu in db.ecus:
    print("==============================")
    print(f"ECU id: {ecu.id}")
    print(f"ECU short_name: {ecu.short_name}")
    print(f"ECU long_name: {ecu.long_name}")
    print(f"ECU CAN Physical Request ID: {hex(ecu.get_receive_id())}")
    print(f"ECU CAN Physical Response ID: {hex(ecu.get_send_id())}")
    print(f"ECU CAN Functional Request ID: {hex(ecu.get_can_func_req_id())}")
    if not ecu.get_doip_logical_gateway_address() is None:
        print(f"ECU DoIP Logical Gateway Address: {hex(ecu.get_doip_logical_gateway_address())}")
    if not ecu.get_doip_logical_functional_address() is None:
        print(f"ECU DoIP Logical Functional Address: {hex(ecu.get_doip_logical_functional_address())}")
    print("==============================")

    # electronicControlUnit.services = services
    for s in ecu.services:
        # service = Service()
        # service.id = s.id
        # service.short_name = s.short_name
        # service.long_name = s.long_name
        # service.description = s.description

        print(f"Service id: {s.id}")
        print(f"Service short_name: {s.short_name}")
        print(f"Service long_name: {s.long_name}")

        print(f"\tRequest id: {s.request.id}")
        print(f"\tRequest short_name: {s.request.short_name}")
        print(f"\tRequest long_name: {s.request.long_name}")
        print(f"\tRequest is_visible: {s.request.is_visible}")
        print(f"\tRequest bit_length: {s.request.bit_length}")

        for request_parameter in s.request.parameters:
            print("\t\t---------------")
            print(f"\t\tRequest Parameter semantic: {request_parameter.semantic}")
            print(f"\t\tRequest Parameter short_name: {request_parameter.short_name}")
            print(f"\t\tRequest Parameter long_name: {request_parameter.long_name}")
            print(f"\t\tRequest Parameter parameter_type: {request_parameter.parameter_type}")
            print(f"\t\tRequest Parameter byte_position: {request_parameter.byte_position}")
            print(f"\t\tRequest Parameter bit_position: {request_parameter.bit_position}")
            print(f"\t\tRequest Parameter bit_length: {request_parameter.bit_length}")
            if hasattr(request_parameter, 'coded_value'):
                print(f"\t\tRequest Parameter coded_value: {request_parameter.coded_value}")
            if hasattr(request_parameter, 'internal_data_type'):
                print(f"\t\tRequest Parameter internal_data_type: {request_parameter.internal_data_type}")
            print("\t\t---------------")

        if hasattr(s, 'positive_responses'):
            for positive_response in s.positive_responses:
                print(f"\tPositive Response id: {positive_response.id}")
                print(f"\tPositive Response response_type: {positive_response.response_type}")
                print(f"\tPositive Response short_name: {positive_response.short_name}")
                print(f"\tPositive Response long_name: {positive_response.long_name}")
                print(f"\tPositive Response is_visible: {positive_response.is_visible}")
                print(f"\tPositive Response bit_length: {positive_response.bit_length}")

                for positive_response_parameter in positive_response.parameters:
                    print("\t\t---------------")
                    print(f"\t\tPositive Response Parameter semantic: {positive_response_parameter.semantic}")
                    print(f"\t\tPositive Response Parameter short_name: {positive_response_parameter.short_name}")
                    print(f"\t\tPositive Response Parameter long_name: {positive_response_parameter.long_name}")
                    print(
                        f"\t\tPositive Response Parameter parameter_type: {positive_response_parameter.parameter_type}")
                    print(f"\t\tPositive Response Parameter byte_position: {positive_response_parameter.byte_position}")
                    print(f"\t\tPositive Response Parameter bit_position: {positive_response_parameter.bit_position}")
                    print(f"\t\tPositive Response Parameter bit_length: {positive_response_parameter.bit_length}")
                    if hasattr(positive_response_parameter, 'coded_value'):
                        print(f"\t\tPositive Response Parameter coded_value: {positive_response_parameter.coded_value}")
                    if hasattr(positive_response_parameter, 'internal_data_type'):
                        print(
                            f"\t\tPositive Response Parameter internal_data_type: {positive_response_parameter.internal_data_type}")
                    print("\t\t---------------")

        if hasattr(s, 'negative_responses'):
            for negative_response in s.negative_responses:
                print(f"\tNegative Response id: {negative_response.id}")
                print(f"\tNegative Response response_type: {negative_response.response_type}")
                print(f"\tNegative Response short_name: {negative_response.short_name}")
                print(f"\tNegative Response long_name: {negative_response.long_name}")
                print(f"\tNegative Response is_visible: {negative_response.is_visible}")
                print(f"\tNegative Response bit_length: {negative_response.bit_length}")

                for negative_response_parameter in negative_response.parameters:
                    # print("functions: ", list_callable_functions(negative_response_parameter))
                    # print("attributes: ", list_public_attributes(negative_response_parameter))
                    print("\t\t---------------")
                    print(f"\t\tNegative Response Parameter semantic: {negative_response_parameter.semantic}")
                    print(f"\t\tNegative Response Parameter short_name: {negative_response_parameter.short_name}")
                    print(f"\t\tNegative Response Parameter long_name: {negative_response_parameter.long_name}")
                    print(
                        f"\t\tNegative Response Parameter parameter_type: {negative_response_parameter.parameter_type}")
                    print(f"\t\tNegative Response Parameter byte_position: {negative_response_parameter.byte_position}")
                    print(f"\t\tNegative Response Parameter bit_position: {negative_response_parameter.bit_position}")
                    print(f"\t\tNegative Response Parameter bit_length: {negative_response_parameter.bit_length}")
                    if hasattr(negative_response_parameter, 'coded_value'):
                        print(f"\t\tNegative Response Parameter coded_value: {negative_response_parameter.coded_value}")
                    if hasattr(negative_response_parameter, 'internal_data_type'):
                        print(
                            f"\t\tNegative Response Parameter internal_data_type: {negative_response_parameter.internal_data_type}")
                    print("\t\t---------------")

        print("==============================")
