# SPDX-License-Identifier: MIT
# Copyright (c) 2022 MBition GmbH

from typing import Union


class Message:
    """A CAN message with its interpretation."""

    def __init__(self,
                 coded_message: Union[bytes, bytearray],
                 service,
                 structure,
                 param_dict: dict):
        """
        Parameters
        ----------
        coded_message : bytes or bytearray
        service : DiagService
        structure : Request or Response
        param_dict : dict
        """
        self.coded_message = coded_message
        self.service = service
        self.structure = structure
        self.param_dict = param_dict

    def __getitem__(self, key: str):
        return self.param_dict[key]

    def __str__(self):
        param_string = ", ".join(map(lambda param: f"{param[0]}={repr(param[1])}",
                                     self.param_dict.items()))
        return f"{self.structure.short_name}({param_string})"

    def __repr__(self):
        return self.__str__()
