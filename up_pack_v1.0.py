import os
import json
import datetime
import time
import zipfile


# 文件类
class File:

    def __init__(self, path, name, size, update_time):
        self.path = path
        self.name = name
        self.size = size
        self.update_time = update_time


# 获取配置信息
def get_config_info(config_name, config_file_path):
    value = ""
    with open(config_file_path, encoding='utf-8') as fp:
        lines = (line for line in fp if not line.startswith('__'))
        config = json.loads(''.join(lines))
        if config_name == "zip_file_name":
            value = config[config_name] + "_" + datetime.datetime.now().strftime("%m.%d.%H")
        elif config_name == "allow_extension" or config_name == "project_path" or config_name == "ignore_path":
            value = config[config_name].split(",")
        else:
            value = config[config_name]
    return value


# 将指定文件压缩成指定名称的zip包
def zip_files(zip_name: str, files: list[File]):
    i = 0
    while True:
        if i == 0:
            new_zip_name = zip_name
        else:
            new_zip_name = zip_name + '(' + str(i) + ')'
        if not os.path.exists(new_zip_name + ".zip"):
            break
        else:
            i += 1
    with zipfile.ZipFile(new_zip_name + ".zip", mode='w', compression=zipfile.ZIP_DEFLATED) as z:
        for file in files:
            # 将当前文件路径转化为相对路径
            arcname = os.path.relpath(file.path, start=os.path.dirname(__file__))
            # 将文件夹入zip文件
            if os.path.isdir(file.path):
                z.write(file.path, arcname=arcname)
            else:
                # 写入单个文件到zip中
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + "up_pack_v1.0: write to zip:", file.path)
                z.write(file.path, arcname=arcname)
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + "up_pack_v1.0:", new_zip_name, " success")
    return


# 初始化或更新文件信息json
def init_file_info(files: list[File]):
    file_infos = []
    for item in files:
        # 获取文件信息，例如文件名、大小、创建时间等
        # print("file info:", item.path)
        info = {'path': item.path, 'name': item.name, 'size': item.size, 'update_time': item.update_time}
        file_infos.append(info)
    with open(file_info_path, 'w') as f:
        json.dump(file_infos, f, indent=4)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + "up_pack_v1.0: file_info.json has been updated")


# 根据配置获取当前符合条件的文件集合
def get_cur_files(current_path, allow_extension, project_path, ignore_path):
    files = []
    for root, dirs, filenames in os.walk(current_path):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in allow_extension):
                file_path = os.path.join(root, filename)
                if any(x in file_path for x in project_path) and not any(x in file_path for x in ignore_path):
                    files.append(file_path)
    file_infos = []
    for file_path in files:
        file_infos.append(
            File(file_path, os.path.basename(file_path), os.path.getsize(file_path),
                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(os.path.getmtime(file_path)))))
    return file_infos


def load_org_files_info(json_filename: str):
    # 读取 JSON 文件生成的文件信息列表
    with open(json_filename, mode='r', encoding='utf-8') as f:
        data = json.load(f)

    file_info_list = []
    for item in data:
        file_info_list.append(File(item['path'], item['name'], item['size'], item['update_time']))

    return file_info_list


# 将当前文件信息与上一版本的文件信息比对，完全相同则从当前文件列表删除
def file_compare(org_files: list[File], cur_files: list[File]):
    up_files = []
    # 创建一个老版本的文件路径映射集合
    org_dict = {f.path: f for f in org_files}
    # 然后遍历当前文件列表，比较其与原始文件列表中相同路径处的对象是否有区别
    for cf in cur_files:
        of = org_dict.get(cf.path)
        if of is None or of.size != cf.size or of.update_time != cf.update_time:
            # 如果当前文件在原始文件列表中存在，且大小和修改时间均相等，则认为该文件没有改动，从当前列表中删除。
            up_files.append(cf)
    return up_files


if __name__ == '__main__':
    print("========================================up_pack_v1.0 Start =========================================")
    # 初始化所需配置 初始化file_infos.json
    current_path = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_path, "up_pack_config.json")
    zip_name = os.path.join(current_path, get_config_info("zip_file_name", config_path))
    # 声明变量, 用于指向 MSBuild 所在路径.
    msbuild_path = get_config_info("msbuild_path", config_path)
    # msbuild_path = r'"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"'
    # 声明变量, 指定你的解决方案文件的目录
    sln_folder_path = get_config_info("sln_folder_path", config_path)
    # 声明变量, 指定你的解决方案文件的名称
    sln_name = get_config_info("sln_name", config_path)
    # 声明变量, 指定输出目录
    # output_path = r'C:\output\directory'
    # 组装命令行字符串
    # build_cmd = f'{msbuild_path} {os.path.join(sln_folder_path, sln_name)} /p:Configuration=Release /t:Clean;Rebuild /p:OutputPath={output_path}'
    build_cmd = f'"{msbuild_path}" {os.path.join(sln_folder_path, sln_name)} /p:Configuration=Debug /t:Clean;Rebuild'
    # 执行构建
    print(f'Running build command: {build_cmd}')
    os.system(build_cmd)
    user_input = input("编译结束,请根据编译结果决定是(Y)否(除Y以外任意键)打包: ")
    if user_input.upper() == "Y":
        allow_extension = get_config_info("allow_extension", config_path)
        project_path = get_config_info("project_path", config_path)
        ignore_path = get_config_info("ignore_path", config_path)
        file_info_path = os.path.join(current_path, "up_pack_files_info.json")
        # 获取当前路径下指定范围文件集合
        current_files = get_cur_files(current_path, allow_extension, project_path, ignore_path)
        # 不存在json文件则初始化 且全量压包
        if not (os.path.exists(file_info_path)):
            files = init_file_info(current_files)
            zip_files(zip_name=zip_name, files=current_files)
        else:
            # 获取文件信息与配置文件比较 返回更新或新增的文件列表
            orginal_files = load_org_files_info(file_info_path)
            up_files = file_compare(org_files=orginal_files, cur_files=current_files)
            if len(up_files) == 0:
                print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ": " + "up_pack_v1.0: 无更新文件")
            else:
                zip_files(zip_name=zip_name, files=up_files)
                # 更新json表
                init_file_info(current_files)
    print("========================================up_pack_v1.0 Finish ========================================")
    os.system("pause")
