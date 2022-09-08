from __future__ import annotations
import os
import shutil
import asyncio

class Directory:
    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(path)
        self.name = ''
        self.files = {}
        self.directories = {}
        self._exists()
        self._instanceExistingFiles()
        self._redifineAtributes()

    def _exists(self) -> None:
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def _instanceExistingFiles(self) -> None:
        for element in os.listdir(self.path):
            path = f'{self.path}/{element}'
            if os.path.isfile(path):
                f = File(path)
                self.files.update({f'{f.name}{f.extension}' : f})
            else:
                d = Directory(path)
                self.directories.update({d.name : d})

    def _redifineAtributes(self) -> None:
        self.name = self.path.split('/')[-1]

    def newDir(self, name: str) -> Directory:
        for dir in self.directories.values():
            if dir.name == name:
                raise FileExistsError (f'Error. There is already a directory named {dir.name} in {self.path}')
        new_dir = Directory(f'{self.path}/{name}')
        self.directories.update({new_dir.name : new_dir})
        return new_dir

    def newFile(self, name: str) -> File:
        for file in self.files.values():
            if f'{file.name}{file.extension}' == name:
                raise FileExistsError (f'Error. There is already a file named {file.name} in {self.path}')
        f = File(f'{self.path}/{name}')
        self.files.update({f'{f.name}{f.extension}' : f})
        return f

    def data(self) -> dict:
        data = {
            'selfData': self.selfData(),
            'contentData': self.contentData()
        }
        return data

    def selfData(self) -> dict:
        data = {
            'path': self.path,
            'name': self.name
        }
        return data

    def contentData(self) -> dict:
        content = {}
        for file in self.files.values():
            content.update({f'{file.name}_file': file.data()})
        for dir in self.directories.values():
            content.update({f'{dir.name}_dir': dir.data()})
        return content

    def removeFile(self, file: File) -> None:
        try:
            self.files.pop(f'{file.name}{file.extension}')
            os.remove(file.path)
        except IndexError as e:
            print(f'Error when trying to delete file. Please check if the file exists in {self.path}. {e}')

    def removeFiles(self, *args: File) -> None:
        for arg in args:
            self.removeFile(arg)

    def removeAllFiles(self) -> None:
        if self.files != {}:
            self.removeFiles(*list(self.files.values()))

    def removeDir(self, dir: Directory) -> None:
        try:
            dir.empty()
            self.directories.pop(dir.name)
            os.rmdir(dir.path)
        except IndexError as e:
            print(f'Error when trying to delete directory. Please check if the directory exists in {self.path}. {e}')
        except OSError as e:
            print(f'Error when trying to delete directory. Please check if the directory {self.path} is empty. {e}')

    def removeDirs(self, *args: Directory) -> None:
        for arg in args:
            self.removeDir(arg)

    def removeAllDirs(self):
        if self.directories != {}:
            self.removeDirs(*list(self.directories.values()))

    def empty(self) -> None:
        self.removeAllDirs()
        self.removeAllFiles()

    async def addFiles(self, *args: File) -> Directory:
        for file in args:
            await file.copy(self)
        return self

    async def addDirectories(self, *args: Directory) -> Directory:
        for dir in args:
            await dir.copy(self)
            #self.directories.update({dir.name : dir})
        return self

    async def copyFilesTo(self, dir: Directory) -> None:
        for file in self.files.values():
            await file.copy(dir)

    async def copyDirsTo(self, dir: Directory) -> None:
        for directory in self.directories.values():
            await directory.copy(dir)
            dir.directories.update({directory.name : directory})

    async def copyAllTo(self, dir: Directory) -> None:
        await self.copyFilesTo(dir)
        await self.copyDirsTo(dir)

    async def copy(self, dir: Directory) -> Directory:
        a = dir.newDir(self.name)
        await self.copyAllTo(a)

    def filesList(self) -> list:
        return list(self.files.values())

    def dirList(self) -> list:
        return list(self.directories.values())

    def findDirs(self, names: list(str), deepLevel = -1, i = 1) -> list:
        matches = []
        if 0 < i <= deepLevel or deepLevel == -1:
            for dir in self.directories.values():
                for name in names:
                    if dir.name == name:
                        matches.append(dir)
                i = i + 1
                matches.extend(dir.findFilesByExtension(names, deepLevel, i))
        return matches

    def findFilesByName(self, names: list(str), deepLevel = -1, i = 1) -> list:
        matches = []
        if 0 < i <= deepLevel or deepLevel == -1:
            for file in self.files.values():
                for name in names:
                    if file.name == name:
                        matches.append(file)
            for dir in self.directories.values():
                i = i + 1
                matches.extend(dir.findFilesByExtension(names, deepLevel, i))
        return matches

    def findFilesByExtension(self, extensions: list, deepLevel = -1, i = 1) -> list:
        matches = []
        if 0 < i <= deepLevel or deepLevel == -1:
            for file in self.files.values():
                for extension in extensions:
                    if file.extension == extension:
                        matches.append(file)
            for dir in self.directories.values():
                i = i + 1
                matches.extend(dir.findFilesByExtension(extensions, deepLevel, i))
        return matches

    def _levelBuilding(self, folder: Directory, deepLevel = -1, i = 1, l = []) -> list:
        if 0 < i <= deepLevel or deepLevel == -1:
            level_list = l
            folder._printLevel(level_list)
            print(f'|')
            for file in folder.files.values():
                folder._printLevel(level_list)
                print(f'|-- 📄 {file.name}{file.extension}')
            for dir in folder.directories.values():
                dir._printLevel(level_list)
                print(f'|')
                dir._printLevel(level_list)
                print(f'|-- 📁 {dir.name}')
                if dir == list(folder.directories.values())[-1]:
                    level_list.append('    ')
                else:
                    level_list.append('|   ')
                i = i + 1
                dir._levelBuilding(dir, deepLevel, i, level_list)
                i = i - 1
                level_list.pop(-1)

    def _printLevel(self, list):
        for element in list:
            print(element, end = '')

    def tree(self, levels = -1):
        level = 0
        print('')
        print(f'🛣️ {self.path}')
        print('')
        print(f'📁 {self.name}')
        self._levelBuilding(self, levels)
        print('')
###################################################################

class File:
    def __init__(self, path: str) -> None:
        self.path = os.path.abspath(path)
        self.dirpath = ''
        self.name = ''
        self.extension = ''
        self._exists()

    def _exists(self) -> None:
        if not os.path.exists(self.path):
            try: open(self.path, 'x')
            except FileNotFoundError as e:
                raise FileNotFoundError(f'Error when trying to create the file. {e}')
        self._redifineAtributes()

    def _redifineAtributes(self) -> None:
        self.extension = os.path.splitext(self.path)[1]
        self.name = os.path.basename(self.path).replace(self.extension, '')
        self.dirpath = os.path.dirname(self.path)

    def data(self) -> dict:
        data = {
            'dirpath': self.dirpath,
            'path': self.path,
            'name': self.name,
            'extension': self.extension
        }
        return data

    async def copy(self, dir: Directory) -> File:
        with open(self.path, 'rb') as forigin:
            new_path = f'{dir.path}/{self.name}{self.extension}'
            copy_string = ''
            while os.path.exists(new_path):
                copy_string = f'{copy_string}__copy'
                new_path = f'{dir.path}/{self.name}{copy_string}{self.extension}'
            with open(new_path, 'wb') as fdestination:
                await asyncio.to_thread(shutil.copyfileobj, forigin, fdestination)
            copied_file = File(new_path)
            dir.files.update({copied_file.name : copied_file})
        return copied_file

    def rename(self, name: str) -> File:
        new = f'{self.dirpath}/{name}{self.extension}'
        os.rename(self.path, new)
        self.path = new
        self._redifineAtributes()
        return self