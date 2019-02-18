# import os
#
#
# class FileAssist(object):
#
#
#     def __init__(self):
#         # 需要计算的代码格式
#         self.code_type = [".py"]
#         self.code_dict = {}
#
#     def get_files(self, ospath):
#         files = os.listdir(ospath)
#         for f in files:
#             # 拼接路径
#             # mypath = os.path.join(ospath, f)
#             # if os.path.isfile(mypath):
#             #
#             #     # if(mypath.find("N遍代码") != -1):
#             #         ext = os.path.splitext(mypath)
#             #         if ext[1] in self.code_type:
#             #             self.code_dit[mypath] = 0
#
#             # if os.path.isdir(mypath):
#             #     self.get_files(mypath)  # 递归
#
#             fname = os.path.splitext(f)
#             if fname[1] == '.py':
#                 pass
#
#
#     def get_code_list(self):
#         for path, count in self.code_dict.items():
#             with open(path, "rb") as f:
#                 num = 0
#                 while True:
#                     content = f.readline()
#                     if content:
#                         if len(content.strip()) > 0:
#                             num += 1
#                     else:
#                         break
#                 self.code_dict[path] = num
#
#     def print_dit(self):
#         num = 0
#         for key, value in self.code_dict.items():
#             num += value
#             print("%s的代码行数是：%d" % (key, value))
#
#         return num
#
#
#
# #测试
# f=FileAssist()
# f.get_files("D:\\python22期就业班")
# f.get_code_list()
# num = f.print_dit()
# print(num)