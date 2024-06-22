import os
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET

CRS = """GEOGCS["WGS84(DD)", DATUM["WGS84", SPHEROID["WGS84", 6378137.0, 298.257223563]], PRIMEM["Greenwich", 0.0], UNIT["degree", 0.017453292519943295], AXIS["Geodetic longitude", EAST], AXIS["Geodetic latitude", NORTH], AUTHORITY["EPSG","4326"]]"""


class GPT:
    def __init__(self, path: os.PathLike | str) -> None:
        """
        Initialize the GPT class with the given path to the SeaDAS gpt file.

        Args:
            path (os.PathLike | str): The path to the SeaDAS gpt file.

        Raises:
            Exception: If the SeaDAS gpt file does not exist.
        """
        if type(path) == str:
            self.path = Path(path)
        else:
            self.path = path
        if not os.path.exists(self.path):
            raise Exception(
                """
                The SeaDAS gpt file does not exist.
                """
            )

    def reproject(self, ifile: os.PathLike | str, ofile: os.PathLike | str, config: dict) -> None:
        """
        Reprojects the input file to a new coordinate reference system (CRS) using the SeaDAS GPT tool.

        Args:
            ifile (os.PathLike | str): The path to the input file to be reprojected.
            ofile (os.PathLike | str): The path to the output file where the reprojected data will be saved.
            config (dict): A dictionary containing the configuration parameters for the reprojecting operation.

        Returns:
            None

        Raises:
            Exception: If the input file does not exist.

        """
        if type(ifile) == str:
            ifile = os.path.realpath(ifile)
        if not os.path.exists(ifile):
            raise Exception(
                """
                The input file does not exist.
                """
            )
        if type(ofile) == str:
            ofile = os.path.realpath(ofile, strict=False)
        args = []
        args.append(self.path)
        with tempfile.NamedTemporaryFile(suffix='.xml', delete=False) as f:
            node_graph([
                {
                    'id': "read",
                    'operator': 'read',
                    'config': {
                        'file':  str(ifile)
                    }
                },
                {
                    'id': "reproject",
                    'operator': 'reproject',
                    'config': {
                        'source': 'read',
                        **config
                    }
                },
                {
                    'id': "write",
                    'operator': 'write',
                    'config': {
                        'source': 'reproject',
                        'file': str(ofile)
                    }
                },
            ]).write(f)
            f.close()
            args.append(f.name)
            subprocess.run(args=args)


def node_graph(g) -> ET.ElementTree:
    """
    Generate the function comment for the given function body in a markdown code block with the correct language syntax.

    Args:
        g (list): A list of dictionaries representing the graph nodes.

    Returns:
        ET.ElementTree: The root element of the XML tree representing the graph.

    """
    funcs = {
        'read': node_read,
        'write': node_write,
        'reproject': node_reproject
    }
    graph = ET.Element('graph')
    root = ET.ElementTree(graph)
    version = ET.SubElement(graph, 'version')
    version.text = '1.0'
    for n in g:
        node = prepare_op_node(n['id'], n['operator'], graph)
        funcs[n['operator']](node, n.get('config', {}))
    return root


def prepare_op_node(id: str, op: str, parent: ET.Element) -> ET.Element:
    """
    Create and return an XML node element representing an operation with the given ID and operator.

    Parameters:
        id (str): The ID of the node.
        op (str): The operator of the node.
        parent (ET.Element): The parent element to which the node will be added.

    Returns:
        ET.Element: The newly created node element.
    """
    node = ET.SubElement(parent, 'node')
    node.set('id', id)
    operator = ET.SubElement(node, 'operator')
    operator.text = op
    return node


def node_reproject(node: ET.Element, config: dict) -> None:
    """
    A function to reproject the node with the given configuration parameters.

    Args:
        node (ET.Element): The node to reproject.
        config (dict): A dictionary containing the configuration parameters.
            It includes 'source', 'resampling', 'orientation', 'pixelSizeX', 'pixelSizeY',
            'orthorectify', 'noDataValue', 'includeTiePointGrids', 'addDeltaBands',
            'applyValidPixelExpression', 'retainValidPixelExpression', and 'format'.

    Returns:
        None
    """
    sources = ET.SubElement(node, 'sources')
    sourceProduct = ET.SubElement(sources, 'sourceProduct')
    sourceProduct.text = config['source']
    parameters = ET.SubElement(node, 'parameters')
    crs = ET.SubElement(parameters, 'crs')
    crs.text = CRS
    resampling = ET.SubElement(parameters, 'resampling')
    resampling.text = config.get('resampling', 'Nearest')
    orientation = ET.SubElement(parameters, 'orientation')
    orientation.text = config.get('orientation', '0.0')
    pixelSizeX = ET.SubElement(parameters, 'pixelSizeX')
    pixelSizeX.text = str(config.get('pixelSizeX'))
    pixelSizeY = ET.SubElement(parameters, 'pixelSizeY')
    pixelSizeY.text = str(config.get('pixelSizeY'))
    orthorectify = ET.SubElement(parameters, 'orthorectify')
    orthorectify.text = config.get('orthorectify', 'false')
    noDataValue = ET.SubElement(parameters, 'noDataValue')
    noDataValue.text = config.get('noDataValue', 'NaN')
    includeTiePointGrids = ET.SubElement(parameters, 'includeTiePointGrids')
    includeTiePointGrids.text = config.get('includeTiePointGrids', 'true')
    addDeltaBands = ET.SubElement(parameters, 'addDeltaBands')
    addDeltaBands.text = config.get('addDeltaBands', 'false')
    applyValidPixelExpression = ET.SubElement(
        parameters, 'applyValidPixelExpression')
    applyValidPixelExpression.text = config.get(
        'applyValidPixelExpression', 'true')
    retainValidPixelExpression = ET.SubElement(
        parameters, 'retainValidPixelExpression')
    retainValidPixelExpression.text = config.get(
        'retainValidPixelExpression', 'true')
    if config.get('format', None):
        f = ET.SubElement(parameters, 'format')
        f.text = config['format']


def node_write(node: ET.Element, config: dict) -> None:
    """
    Modifying the node to write operation in GPT.

    Args:
        node (ET.Element): The XML node to which the 'sources' and 'parameters' elements will be added.
        config (dict): A dictionary containing the configuration parameters.

    Returns:
        None
    """
    sources = ET.SubElement(node, 'sources')
    source = ET.SubElement(sources, 'source')
    source.text = config['source']
    parameters = ET.SubElement(node, 'parameters')
    file = ET.SubElement(parameters, 'file')
    file.text = config['file']
    if config.get('format', None):
        f = ET.SubElement(parameters, 'format')
        f.text = config['format']


def node_read(node: ET.Element, config) -> None:
    """
    A function to read the node with the given configuration parameters.
    Args:
        node (ET.Element): The node to read.
        config (dict): A dictionary containing the configuration parameters.
            It includes 'file' as the file to read and 'format' as the format if available.
    Returns:
        None
    """
    parameters = ET.SubElement(node, 'parameters')
    file = ET.SubElement(parameters, 'file')
    file.text = config['file']
    if config.get('format', None):
        f = ET.SubElement(parameters, 'format')
        f.text = config['format']
