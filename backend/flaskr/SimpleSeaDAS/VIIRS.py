import os
from .OCSSW import OCSSW


class VIIRS:
    @staticmethod
    def generateL2(ocssw: OCSSW, l1a: str, geo: str, out: str, suite: str = 'OC', **kwargs) -> None:
        """generates L2 file using l2gen from OCSSW package

        Args:
            ocssw (OCSSW): ocssw object with filled root path
            l1a (str): path to viirs l1a file
            geo (str): path to viirs geo file
            out (str): path where to store l2 file
            suite (str, optional): suite is group of standard parameters and products. Defaults to 'OC'. More in SeaDAS documentation.

        Returns:
            _type_: path to l2 file
        """
        return ocssw.l2gen(
            {
                'ifile': os.path.realpath(l1a),
                'geofile': os.path.realpath(geo),
                'ofile': os.path.realpath(out, strict=False),
                'suite': suite,
                **kwargs
            }
        )
        # download viirs l1a + geo -> l2gen -> reproject -> save dimap
        # or download several viirs l1a + geo -> l2gen -> reproject -> mosaic -> save dimap
