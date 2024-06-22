from multiprocessing import Pool
from pathlib import Path
import requests
import os
from . import const


class OceanData:
    """
        Interface for finding and downloading data from the Ocean Data Portal.
    """
    base_url = 'https://oceandata.sci.gsfc.nasa.gov'

    def __init__(self, appkey='') -> None:
        self.appkey = appkey

    def __check_keyapp(self) -> None:
        if self.appkey == '':
            raise Exception(
                '''
                Appkey not provided. 
                Get appkey from "https://oceandata.sci.gsfc.nasa.gov/appkey/".
                '''
            )

    def find(self, config: dict) -> list[str]:
        """
        Find data based on the given configuration.

        This function sends a POST request to the Ocean Data Portal API with
        the given configuration parameters. The API returns the file names of
        the data that match the given configuration.

        The configuration parameters must contain the following keys:
            'sensor': A string representing the sensor name.
            'data_type': A string representing the data type.
            'start_date': A datetime object representing the start date.
            'end_date': A datetime object representing the end date.

        If there are no matching files, an empty list is returned. Otherwise,
        a list of strings is returned representing the file names of the data
        that match the given configuration.

        Args:
            config: A dictionary containing the configuration parameters.

        Returns:
            A list of strings representing the search results.
        """
        url = '/api/file_search'
        # Build the data to be sent in the POST request.
        data = {
            'results_as_file': 1,  # Return the results as a file.
            'sensor_id': const.SENSORS[config['sensor']],  # Sensor ID.
            'dtid': const.DATA_TYPES[config['data_type']],  # Data type ID.
            # Start date.
            'sdate': config['start_date'].strftime('%Y-%m-%d %H:%M:%S'),
            # End date.
            'edate': config['end_date'].strftime('%Y-%m-%d %H:%M:%S'),
            'subType': 1  # Subtype.
        }

        # Send the request.
        response = requests.post(f'{self.base_url}{url}', data=data)

        # If the request fails, raise an exception.
        if response.status_code == requests.codes.bad_request:
            raise Exception()

        # Decode the response and split it by lines.
        ans = response.content.decode().split('\n')

        # If the first line is 'No Results Found', return an empty list.
        # Otherwise, return the list of file names.
        if ans[0] == 'No Results Found':
            return []
        return ans

    def download(self, name: str, folder: os.PathLike | str = Path(os.getcwd())) -> str:
        """
        A function to download a file from Ocean Data Portal.

        This function takes a file name and a folder where to download the file.
        If the folder does not exist, it creates it.

        It makes a GET request to the Ocean Data Portal API with the file name
        and the appkey. The response is a StreamedResponse object.

        We use the iter_content method of the StreamedResponse object to read
        the response in chunks of 131072 bytes. This is done to avoid reading the
        whole response into memory at once, which can be memory-intensive.

        We open the file for writing in binary mode ('wb') and write the chunks
        to the file. If the chunk is not empty, we write it to the file.

        The path to the downloaded file is returned.

        Args:
            name: The file name to download.
            folder: The folder where to download the file. If it does not exist,
                it is created. The default value is the current working directory.

        Returns:
            Path to the downloaded file.
        """
        self.__check_keyapp()

        # Check if the folder exists. If not, create it.
        if type(folder) == str:
            folder = Path(folder)
        if not os.path.exists(folder):
            os.makedirs(folder)

        # Build the URL to download the file from.
        url = '/getfile/'
        path = os.path.join(folder, name)

        # Make a GET request to the Ocean Data Portal API.
        r = requests.get(
            f'{self.base_url}{url}{name}',
            data={'appkey': self.appkey},
            stream=True
        )

        # Read the response in chunks of 131072 bytes and write it to the file.
        with open(path, 'wb') as file:
            for chunk in r.iter_content(chunk_size=131072):
                if chunk:
                    file.write(chunk)

        # Return the full path to the downloaded file.
        return path

    def download_severals(self, names: list[str],
                          folder: os.PathLike | str = Path(os.getcwd())) -> list:
        """A function to download several files at once.

        This function creates a pool of workers to download the files in parallel.
        It takes a list of file names and downloads them to the given folder.
        If the folder does not exist, it creates it.

        Args:
            names: A list of file names to download.
            folder: The folder where to download the files. If it does not exist,
                it is created. The default value is the current working directory.

        Returns:
            A list of strings representing the full paths to the downloaded files.
        """
        if type(folder) == str:
            folder = Path(folder)
        if not os.path.exists(folder):
            os.makedirs(folder)
        it = [(name, folder) for name in names]
        pool = Pool()
        # starmap calls the function (self.download) with each tuple in the
        # iterable (it) as a single argument. This is useful when the function
        # takes multiple arguments, but we want to pass a sequence of tuples
        # as arguments.
        # https://docs.python.org/3.7/library/multiprocessing.html#multiprocessing.pool.Pool.starmap
        results = pool.starmap(func=self.download, iterable=it)
        # The results are returned as an iterator, so we need to convert it to
        # a list in order to return it.
        return list(results)
