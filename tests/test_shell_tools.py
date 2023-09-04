# SPDX-License-Identifier: MIT

import unittest
from argparse import Namespace

import odxtools.cli.browse as browse
import odxtools.cli.find as find
import odxtools.cli.list as list


class utilFunctions():

    def list_arguments_and_execution(path_to_pdx_file='.\examples\somersault.pdx',
                                     ecu_variants="all",
                                     print_neg_responses=False,
                                     ecu_services=None,
                                     print_params=False,
                                     print_dops=False,
                                     print_all=False):
        list_args = Namespace(
            pdx_file=path_to_pdx_file,
            variants=ecu_variants,
            global_negative_responses=print_neg_responses,
            services=ecu_services,
            params=print_params,
            dops=print_dops,
            all=print_all)

        list.run(list_args)

    def find_arguments_and_execution(path_to_pdx_file='.\examples\somersault.pdx',
                                     ecu_variants="all",
                                     data=None,
                                     decode=None,
                                     ecu_services=None,
                                     no_details=True,
                                     relaxed_output=False):
        find_args = Namespace(
            pdx_file=path_to_pdx_file,
            variants=ecu_variants,
            data=data,
            decode=decode,
            service_names=ecu_services,
            no_details=no_details,
            relaxed_output=relaxed_output)

        find.run(find_args)


class TestCommandLineTools(unittest.TestCase):

    def test_list_command(self):

        utilFunctions.list_arguments_and_execution()
        utilFunctions.list_arguments_and_execution(ecu_variants=["somersault"])
        utilFunctions.list_arguments_and_execution(print_neg_responses=True)
        utilFunctions.list_arguments_and_execution(print_params=True)
        utilFunctions.list_arguments_and_execution(print_dops=True)
        utilFunctions.list_arguments_and_execution(print_all=True)
        utilFunctions.list_arguments_and_execution(ecu_services="session_start")

    def test_find_command(self):

        utilFunctions.find_arguments_and_execution(ecu_services=["session_start"])
        utilFunctions.find_arguments_and_execution(ecu_services=["session_start"], no_details=False)
        utilFunctions.find_arguments_and_execution(data=["3E 00"])
        utilFunctions.find_arguments_and_execution(data=["3E 00"], ecu_variants=["somersault_lazy"])
        utilFunctions.find_arguments_and_execution(decode=["3E 00"])
        utilFunctions.find_arguments_and_execution(decode=["3E 00"], relaxed_output=True)

    def test_browse_command(self):
        browse_args = Namespace(pdx_file='.\examples\somersault.pdx')
        browse.run(browse_args)


if __name__ == "__main__":
    unittest.main()
