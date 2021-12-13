#!/usr/bin/env python 
# coding:utf-8
#!/usr/bin/env python3
import requests
import webbrowser
import subprocess
import time
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr
from email.mime.application import MIMEApplication #发送附件
import zipfile

project_name = 'VivalnkScience'  # 项目名称
archive_workspace_path = '/Users/weixu/Code/VivaLNKSDK/VivaLnkSDK/VivalnkScience'  # 项目路径
export_directory = '/Users/xuwei/Desktop/打包/FeverScout'  # 导出ipa等文件夹

# 蒲公英账号USER_KEY、API_KEY
USER_KEY = 'xxx'
API_KEY = 'xxx'

# 苹果账号信息
al_tool_path = '/Applications/Xcode.app/Contents/Applications/Application\ ' \
               'Loader.app/Contents/Frameworks/ITunesSoftwareService.framework/Versions/A/Support/altool '
apple_id = 'cyan@vivalnk.com.cn'
generate_password = 'yukp-texu-qqci-jtfv'  # 并非apple_id 登录密码 https://appleid.apple.com/account/manage 点击Generate Password…获取密码

email_vivalnk_server = True

if email_vivalnk_server:
    from_address = 'cyan@vivalnk.com.cn'  # 发送人的地址
    password = 'xw19910812wxpwan'  # 邮箱16位授权码
    to_address = ['846026827@qq.com']  # 收件人地址,可以是多个的
    smtp_server = 'smtp.vivalnk.com.cn'  # 邮箱授权发送服务器
else:
    from_address = '846026827@qq.com'  # 发送人的地址
    password = 'fwbkaqamdbysbbjc'  # 邮箱16位授权码
    to_address = ['846026827@qq.com','cyan@vivalnk.com.cn']  # 收件人地址,可以是多个的
    smtp_server = 'smtp.qq.com'  # 邮箱授权发送服务器


down_url = 'https://www.pgyer.com/pOWZ'  # 蒲公英下载链接

description = '添加C++ Temp'  # 版本更新内容

# 配置 上传 蒲公英还是 App Store
upload_app_store = True


class AutoArchive(object):
    """自动打包并上传到蒲公英,发邮件通知"""
    def __init__(self):
        pass

    def clean(self):
        print("\n\n===========开始clean操作===========")
        start = time.time()
        clean_command = 'xcodebuild clean -workspace %s/%s.xcworkspace -scheme %s -configuration Release' % (
            archive_workspace_path, project_name, project_name)
        clean_command_run = subprocess.Popen(clean_command, shell=True)
        clean_command_run.wait()
        end = time.time()
        # Code码
        clean_result_code = clean_command_run.returncode
        if clean_result_code != 0:
            print("=======clean失败,用时:%.2f秒=======" % (end - start))
        else:
            print("=======clean成功,用时:%.2f秒=======" % (end - start))
            self.archive()

    def archive(self):
        print("\n\n===========开始archive操作===========")

        # 删除之前的文件
        subprocess.call(['rm', '-rf', '%s' % export_directory])
        time.sleep(1)
        # 创建文件夹存放打包文件
        subprocess.call(['mkdir', '-p', '%s' % export_directory])
        time.sleep(1)

        start = time.time()

        # archive_command = 'xcodebuild archive -workspace %s/%s.xcworkspace -scheme %s -configuration Release ' \
        #                   '-archivePath %s ODE_SIGN_IDENTITY=' \
        #                   '%s PROVISIONING_PROFILE=%s' % (
        #                       archive_workspace_path, project_name, project_name,
        #                       export_directory, ios_distribution, profile_uuid)
        archive_command = 'xcodebuild archive -workspace %s/%s.xcworkspace -scheme %s -configuration Release ' \
                          '-archivePath %s' % (
            archive_workspace_path, project_name, project_name, export_directory)
        archive_command_run = subprocess.Popen(archive_command, shell=True)
        archive_command_run.wait()
        end = time.time()
        # Code码
        archive_result_code = archive_command_run.returncode
        if archive_result_code != 0:
            print("=======archive失败,用时:%.2f秒=======" % (end - start))
        else:
            print("=======archive成功,用时:%.2f秒=======" % (end - start))
            # 导出IPA
            self.export()

    def export(self):
        print("\n\n===========开始export操作===========")
        print("\n\n==========请你耐心等待一会~===========")
        start = time.time()
        export_command = 'xcodebuild -exportArchive -archivePath %s.xcarchive -exportPath %s ' \
                         '-exportOptionsPlist %s/ExportOptions.plist' % (
                             export_directory, export_directory,
                             archive_workspace_path)
        export_command_run = subprocess.Popen(export_command, shell=True)
        export_command_run.wait()
        end = time.time()
        # Code码
        export_result_code = export_command_run.returncode
        if export_result_code != 0:
            print("=======导出IPA失败,用时:%.2f秒=======" % (end - start))
        else:
            print("=======导出IPA成功,用时:%.2f秒=======" % (end - start))
            # 删除archive.xcarchive文件
            subprocess.call(['rm', '-rf', '%s.xcarchive' % export_directory])
            path = '%s/%s.ipa' % (export_directory, project_name)
            if upload_app_store:
                self.upload_app_store(path)
                # self.send_email();
            else:
                self.upload(path)

    def upload(self, ipa_path):
        print("\n\n===========开始上传蒲公英操作===========")
        if ipa_path:
            # https://www.pgyer.com/doc/api 具体参数大家可以进去里面查看,
            url = 'http://www.pgyer.com/apiv1/app/upload'
            data = {
                'uKey': USER_KEY,
                '_api_key': API_KEY,
                'installType': '1',
                'updateDescription': description
            }
            files = {'file': open(ipa_path, 'rb')}
            r = requests.post(url, data=data, files=files)
            if r.status_code == 200:
                # 是否需要打开浏览器
                # self.open_browser(self)
                self.send_email()
        else:
            print("\n\n===========没有找到对应的ipa===========")
            return

    # 4.上传到App Store
    def upload_app_store(self, ipa_path):
        start = time.time()
        if os.path.exists(ipa_path):
            print('正在验证ipa文件,请稍后...')
            r1 = os.system('%s -v -f %s -u %s -p %s -t ios [--output-format xml]' % (
            al_tool_path, ipa_path, apple_id, generate_password))
            end = time.time()
            if r1 == 0:
                print("=======验证ipa文件成功,用时:%.2f秒=======" % (end - start))
                print('正在上传ipa文件,请稍后...')
                start1 = time.time()
                r2 = os.system('%s --upload-app -f %s -t ios -u %s -p %s [--output-format xml]' % (
                    al_tool_path, ipa_path, apple_id, generate_password))
                end1 = time.time()
                if r2 == 0:
                    print("=======上传ipa文件到App Store成功,用时:%.2f秒=======" % (end1 - start1))
                    self.send_email()
                else:
                    print('上传ipa文件到App Store失败')
            else:
                print('验证ipa文件失败')
        else:
            print('没有找到.ipa文件')

    @staticmethod
    def open_browser():
        webbrowser.open(down_url, new=1, autoraise=True)

    @staticmethod
    def _format_address(s):
        name, address = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), address))

    def get_zip_file(self,input_path, result):
        """
        对目录进行深度优先遍历
        :param input_path:
        :param result:
        :return:
        """
        files = os.listdir(input_path)
        print(files)
        for file in files:
            if os.path.isdir(input_path+'/'+file):
                get_zip_file(input_path+'/'+file, result)
            else:
                result.append(input_path+'/'+file)

    def zip_file_path(self,input_path, output_path, output_name):
        """
        压缩文件
        :param input_path: 压缩的文件夹路径
        :param output_path: 解压（输出）的路径
        :param output_name: 压缩包名称
        :return:
        """
        f = zipfile.ZipFile(output_path + '/' + output_name, 'w', zipfile.ZIP_DEFLATED)
        filelists = []
        self.get_zip_file(input_path, filelists)
        print(filelists)
        for file in filelists:
            f.write(file)
        # 调用了close方法才会保证完成压缩
        f.close()
        return output_path + r"/" + output_name

    def send_email(self):
        strFrom = self._format_address(from_address)

        strTo = list()
        # 原来是一个纯邮箱的list，现在如果是一个["jayzhen<jayzhen@jz.com>"]的list给他格式化
        try:
            for a in to_address:
                strTo.append(self._format_address(a))
        except Exception as e:
            # 没有对a和toadd进行type判断，出错就直接还原
            strTo = to_address

        msgRoot = MIMEMultipart('related')
        msgRoot.preamble = 'This is a multi-part message in MIME format.'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        # 邮件对象
        plain_text = '最新iOS SDK demo 程序'
        msgText = MIMEText(plain_text, 'plain', 'utf-8')
        msgRoot['Subject'] = Header("iOS SDK demo程序")  # 这是邮件的主题，通过Header来标准化
        msgRoot['From'] = strFrom  # 发件人也是被格式化过的
        msgRoot['to'] = ','.join(strTo)  # 这个一定要是一个str,不然会报错“AttributeError: 'list' object has no attribute 'lstrip'”
        msgAlternative.attach(msgText)

        # 打开附件
        attach_file_name = 'SDK-01_Demo_v1.2.1.0001_iOS.zip'
        attach_file_zip = self.zip_file_path(export_directory,'/Users/xuwei/Desktop/打包',attach_file_name)
        part_attach1 = MIMEApplication(open(attach_file_zip, 'rb').read())
        part_attach1.add_header('Content-Disposition', 'attachment', filename=attach_file_name)  # 为附件命名
        msgRoot.attach(part_attach1)  # 添加附件


        smtp = smtplib.SMTP(smtp_server, 25)
        smtp.set_debuglevel(0)
        smtp.login(from_address, password)
        # 这里要注意了，这里的from_address和to_address和msgRoot['From'] msgRoot['to']的区别
        smtp.sendmail(from_address, to_address, msgRoot.as_string())
        smtp.quit();
        print("===========邮件发送成功===========")


if __name__ == '__main__':
    # if len(description) == 0:
    #     description = input("请输入更新内容:")
    archive = AutoArchive()
    archive.clean()
    # archive.send_email();