import json
from dotenv import load_dotenv
import os
from os.path import basename
from os import walk
from zipfile import ZipFile
import click
import threading
import requests
import database
import numpy as np
import pathlib
import time
from prettytable import PrettyTable
import xml.etree.ElementTree as elementTree

load_dotenv()


class Dataset:

    def __init__(self):

        self.url = os.environ["API_URL_CUSTOMERS"]

        self.payload = {'username': os.environ["LOGIN_USERNAME"],
                        'password': os.environ['LOGIN_PASSWORD']}

        self.files = [
        ]

        if os.environ['BASIC_AUTH'] is not None:
            self.headers = {
                'Authorization': 'Basic ' + os.environ['BASIC_AUTH'],
            }

        self.result = ''

        self.type = 'customers'

        self.extension = 'xml'

    def fetch(self, tasks, job_id):

        threads = []

        for x in tasks:
            # click.secho(f"Thread for {x} page!")
            threads.append(
                threading.Thread(target=self.fetch_page, args=(x, job_id,)))
            threads[-1].start()  # start the thread we just created

        for t in threads:
            t.join()

    def fetch_page(self, page, job_id):
        response = requests.request("POST", self.url + str(page), headers=self.headers,
                                    data=self.payload, files=self.files)

        if response.status_code == 200:
            result = {
                "status": response.status_code,
                "text": response.text,
                "total": response.headers['X-Migrations-Total'],
                "page": int(page),
                "job_id": int(job_id)
            }
            self.create_item(result)
            if job_id != 0:
                self.save_result(result, self.extension)
        else:
            result = {
                "status": response.status_code,
                "text": response.text,
                "page": int(page),
                "job_id": int(job_id)
            }
            self.create_item(result)
        return result

    def init_job(self):

        result = self.get_unfinished_jobs({'type': self.type})

        if result is None:
            page_result = self.fetch_page(1, 0)

            returnData = {
                "state": "created",
                "status": "new",
                "type": self.type,
                "size": int(page_result["total"])
            }
            newJob = self.create_job(returnData)
            returnData["id"] = newJob
            return returnData
        else:
            returnData = {
                "state": "exists",
                "id": result[0],
                "status": result[1],
                "size": result[2]
            }
            return returnData

    def run_job(self, job):
        jobDetails = self.get_job(job)
        jobItems = self.get_job_items(job)

        num_of_pages = int(np.ceil(jobDetails[3] / 100))
        range_list = np.arange(1, num_of_pages + 1)

        if not jobItems:
            todo_list = range_list
        else:
            m = np.asmatrix(jobItems)

            existing = m[:, 2].T[0]
            existing = np.squeeze(np.asarray(existing)).astype(int)

            dif1 = np.setdiff1d(range_list, existing)
            dif2 = np.setdiff1d(existing, range_list)

            todo_list = np.concatenate((dif1, dif2))

        num_of_threads = int(os.environ['NUM_OF_THREADS'])
        if num_of_threads <= 0:
            num_of_threads = 1
        if num_of_threads > 10:
            num_of_threads = 10
            click.echo()
            click.echo(click.style(f'Max number of threads is 10, check you config. Continue with 10 threads',
                                   bg="red", fg="white"))
            click.echo()
        size_of_todo = int(len(todo_list) / num_of_threads)  # num_of_threads

        if size_of_todo == 0:
            size_of_todo = 1

        todo_split = np.array_split(todo_list, size_of_todo)

        if not todo_split:
            return None

        self.fetch(todo_split[0], jobDetails[0])

        return todo_split[0].tolist()

    def save_result(self, result, extension):
        job_name = str(f'{int(result["job_id"]):04}')
        file_string = str(f'{int(result["page"]):08}')
        directory_path = str(pathlib.Path(__file__).parent.resolve()) + '/../results/' + self.type + '/job_' + job_name
        pathlib.Path(directory_path).mkdir(parents=True, exist_ok=True)
        file_name = '/' + self.type + '_' + job_name + '_' + file_string + '.' + extension
        file_path = directory_path + file_name
        with open(file_path, 'w') as f:
            f.write(result['text'])

    def run_job_bulk(self, job_status):
        num_of_pages = int(np.ceil(job_status['size'] / 100))

        bar = click.progressbar(
            length=num_of_pages,
            label=str("Fetch data from API...").ljust(30, ' '),
            bar_template="%(label)s  %(bar)s | %(info)s",
            fill_char=click.style("█", fg="cyan"),
            item_show_func=lambda a: '' if len(a) == 0 else 'Processed pages: ' + ' '.join(map(str, a)),
            empty_char=" ",
        )

        bar.update(1, [])
        while True:
            res = self.run_job(job_status)
            bar.update(len(res), res)
            if res is None or len(res) == 0:
                time.sleep(2)
                bar.update(num_of_pages, [])
                break

    def rerun_failed(self, job_status):
        job_status['non_response_code'] = 200
        error_items = self.get_job_items(job_status)

        while len(error_items) > 0:
            x = PrettyTable()
            x.field_names = ["ID", "Job ID", "Page", "Status", "Created at"]
            x.add_rows(error_items)

            click.echo()
            click.echo(x)
            click.echo(
                f'There is some items with error on fetch. Try again with this items?')
            click.echo('Continue? [yn] ', nl=False)
            c = click.getchar()
            click.echo()
            if c == 'y':
                self.clean_failed_items(job_status)
                job_status['non_response_code'] = None
                self.run_job_bulk(job_status)
                click.echo()
                job_status['non_response_code'] = 200
                error_items = self.get_job_items(job_status)
            else:
                click.echo("OK, Bye")
                break

        return len(error_items)

    def __group_files_for_merge(self, params, max_file_size=99.0):
        job_name = str(f'{int(params["id"]):04}')
        directory_path = str(pathlib.Path(__file__).parent.resolve()) + '/../results/' + self.type + '/job_' + job_name
        all_files = list()

        for root, dirs, files in walk(directory_path):
            all_files.extend(files)

        filtered_files = filter(lambda a: a.endswith(self.extension), all_files)
        file_size = 0.0
        i = 0
        tmp_list = []
        chunked_list = []
        sums = 0
        for f in filtered_files:
            sums += 1
            file_size += os.stat(directory_path + '/' + f).st_size / (1024 * 1024)
            if float(file_size) <= float(max_file_size):
                tmp_list.append(f)
            else:
                i += 1
                file_size = 0.0
                chunked_list.append(tmp_list)
                tmp_list = list()
                tmp_list.append(f)

        chunked_list.append(tmp_list)

        return {"chunked_list": chunked_list, "total": all_files}

    def __merge_json_files(self, files_list, params, filename, bar):
        job_name = str(f'{int(params["id"]):04}')
        directory_path = str(pathlib.Path(__file__).parent.resolve()) + '/../results/' + self.type + '/job_' + job_name

        bar.update(1, [])

        result = []
        for f1 in files_list:
            infile = open(directory_path + '/' + f1, 'r')
            result.extend(json.load(infile))
            bar.update(1, [])

        with open(directory_path + '/../' + filename, 'w') as output_file:
            json.dump(result, output_file)

    def __merge_xml_files(self, list_files, params, filename, bar):
        job_name = str(f'{int(params["id"]):04}')
        directory_path = str(pathlib.Path(__file__).parent.resolve()) + '/../results/' + self.type + '/job_' + job_name

        bar.update(1, [])
        tree1 = elementTree.parse(directory_path + '/' + list_files.pop())
        root1 = tree1.getroot()
        while True:
            bar.update(1, [])
            if len(list_files) == 0:
                break

            tree2 = elementTree.parse(directory_path + '/' + list_files.pop())
            root2 = tree2.getroot()
            root1.extend(root2)

        tree1.write(directory_path + '/../' + filename + '.bak')
        correct_data = open(directory_path + '/../' + filename + '.bak').read().replace('ns0:', '').replace(':ns0', '')
        filewrite = open(directory_path + '/../' + filename, 'w')
        filewrite.write(correct_data)
        filewrite.close()
        os.remove(directory_path + '/../' + filename + '.bak')
        self.__prepend_line(directory_path + '/../' + filename, '<?xml version="1.0" encoding="utf-8"?>')

    def merge_files(self, params, max_file_size=99.0):

        data = self.__group_files_for_merge(params, max_file_size)
        list_of_grouped_files = data['chunked_list']

        job_name = str(f'{int(params["id"]):04}')
        directory_path = str(pathlib.Path(__file__).parent.resolve()) + '/../results/' + self.type + '/job_' + job_name

        i = 0

        bar = click.progressbar(
            length=len(data['total']),
            label=str("Processing with " + self.extension + " files...").ljust(30, ' '),
            bar_template="%(label)s  %(bar)s | %(info)s",
            fill_char=click.style("█", fg="green"),
            item_show_func=lambda a: '' if len(a) == 0 else 'Processed files: ' + ' '.join(map(str, a)),
            empty_char=" ",
        )
        result_file_list = []
        for grouped_files in list_of_grouped_files:
            i += 1
            result_file = self.type + '_job_' + job_name + '_' + str(f'{i:04}') + '.' + self.extension
            if self.extension == 'xml':
                self.__merge_xml_files(grouped_files, params, result_file, bar)
            else:
                self.__merge_json_files(grouped_files, params, result_file, bar)

            result_file_list.append(directory_path + '/../' + result_file)

        click.echo()

        bar = click.progressbar(
            length=len(result_file_list),
            label=str("Compressing " + self.extension + " files...").ljust(30, ' '),
            bar_template="%(label)s  %(bar)s | %(info)s",
            fill_char=click.style("#", fg="magenta"),
            item_show_func=lambda a: '' if len(a) == 0 else 'Processed files: ' + ' '.join(map(str, a)),
            empty_char=" ",
        )

        bar.update(1, [])

        result_file_zip = directory_path + '/../' + self.type + '_job_' + job_name + '.zip'

        with ZipFile(result_file_zip, 'w') as zipObj2, bar as bar:
            # Add multiple files to the zip
            for x in result_file_list:
                zipObj2.write(x, basename(x))
                bar.update(1, [basename(x)])
            bar.update(1, [])

        for x in result_file_list:
            os.remove(x)
        click.echo(click.style(f'Zip file iz ready at: {os.path.abspath(result_file_zip)}',
                               bg="green", fg="red"))
        click.echo(click.style(f'Original response from API is ready at: {os.path.abspath(directory_path)}',
                               bg="green", fg="red"))

    def run_job_main(self, job_status):
        self.run_job_bulk(job_status)
        num_of_failed = self.rerun_failed(job_status)
        click.echo()
        if num_of_failed == 0:
            max_file_size = 10.0
            if os.environ["MAX_FILE_SIZE"] is not None:
                max_file_size = float(os.environ["MAX_FILE_SIZE"])
            self.merge_files(job_status, max_file_size)
            click.echo()
        else:
            click.echo(f'Job is not completed')

    @staticmethod
    def __prepend_line(file_name, line):
        """ Insert given string as a new line at the beginning of a file """
        # define name of temporary dummy file
        dummy_file = file_name + '.bak'
        # open original file in read mode and dummy file in write mode
        with open(file_name, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
            # Write given line to the dummy file
            write_obj.write(line + '\n')
            # Read lines from original file one by one and append them to the dummy file
            for line in read_obj:
                write_obj.write(line)
        # remove original file
        os.remove(file_name)
        # Rename dummy file as the original file
        os.rename(dummy_file, file_name)

    @staticmethod
    def clean_failed_items(params):
        conn = database.db_conn()
        return database.clean_failed_items(conn, params)

    @staticmethod
    def get_unfinished_jobs(params):
        conn = database.db_conn()
        return database.get_unfinished_jobs(conn, params)

    @staticmethod
    def cancel_job(params):
        conn = database.db_conn()
        database.update_job_status(conn, params)

    @staticmethod
    def create_job(params):
        conn = database.db_conn()
        return database.create_job(conn, params)

    @staticmethod
    def get_job(params):
        conn = database.db_conn()
        return database.get_job(conn, params)

    @staticmethod
    def create_item(params):
        conn = database.db_conn()
        return database.create_items(conn, params)

    @staticmethod
    def get_job_items(params):
        conn = database.db_conn()
        return database.get_job_items(conn, params)


class Customers(Dataset):
    def __init__(self):
        super().__init__()


class Orders(Dataset):
    def __init__(self):
        super().__init__()
        self.url = os.environ["API_URL_ORDERS"]
        self.type = 'orders'


class Giftcards(Dataset):
    def __init__(self):
        super().__init__()
        self.url = os.environ["API_URL_GIFTCARDS"]
        self.type = 'giftcards'
        self.extension = 'json'


class SorSubscriptions(Dataset):
    def __init__(self):
        super().__init__()
        self.url = os.environ["API_URL_SOR_SUBSCRIPTIONS"]
        self.type = 'sor_subscriptions'
        self.extension = 'json'


class SorOrders(Dataset):
    def __init__(self):
        super().__init__()
        self.url = os.environ["API_URL_SOR_ORDERS"]
        self.type = 'sor_orders'
        self.extension = 'json'
