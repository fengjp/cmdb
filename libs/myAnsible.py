import json
import shutil
from ansible.module_utils.common.collections import ImmutableDict
# 用于读取YAML和JSON格式的文件
from ansible.parsing.dataloader import DataLoader
# 用于存储各类变量信息
from ansible.vars.manager import VariableManager
# 用于导入资产文件
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C
# 操作单个主机信息
from ansible.inventory.host import Host
# 操作单个主机组信息
from ansible.inventory.group import Group


class ResultCallback(CallbackBase):
    """
    重写callbackBase类的部分方法
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.host_ok = {}
        self.host_unreachable = {}
        self.host_failed = {}
        self.task_ok = {}

    def v2_runner_on_unreachable(self, result):
        self.host_unreachable[result._host.get_name()] = result

    def v2_runner_on_ok(self, result, **kwargs):
        self.host_ok[result._host.get_name()] = result

    def v2_runner_on_failed(self, result, **kwargs):
        self.host_failed[result._host.get_name()] = result


class MyAnsiable2():
    def __init__(self,
                 connection='local',  # 连接方式 local 本地方式，smart ssh方式
                 remote_user=None,  # ssh 用户
                 remote_password=None,  # ssh 用户的密码，应该是一个字典, key 必须是 conn_pass
                 private_key_file=None,  # 指定自定义的私钥地址
                 sudo=None, sudo_user=None, ask_sudo_pass=None,
                 module_path=None,  # 模块路径，可以指定一个自定义模块的路径
                 become=None,  # 是否提权
                 become_method=None,  # 提权方式 默认 sudo 可以是 su
                 become_user=None,  # 提权后，要成为的用户，并非登录用户
                 check=False, diff=False,
                 listhosts=None, listtasks=None, listtags=None,
                 verbosity=3,
                 syntax=None,
                 start_at_task=None,
                 inventory=None,
                 hostsresource=None,
                 ):

        # 函数文档注释
        """
        初始化函数，定义的默认的选项值，
        在初始化的时候可以传参，以便覆盖默认选项的值
        """
        context.CLIARGS = ImmutableDict(
            connection=connection,
            remote_user=remote_user,
            private_key_file=private_key_file,
            sudo=sudo,
            sudo_user=sudo_user,
            ask_sudo_pass=ask_sudo_pass,
            module_path=module_path,
            become=become,
            become_method=become_method,
            become_user=become_user,
            verbosity=verbosity,
            listhosts=listhosts,
            listtasks=listtasks,
            listtags=listtags,
            syntax=syntax,
            start_at_task=start_at_task,
        )

        # 三元表达式，假如没有传递 inventory, 就使用 "localhost,"
        # sources这个我们知道这里是设置hosts文件的地方，它可以是一个列表里面包含多个文件路径且文件真实存在，在单纯的执行ad-hoc的时候这里的
        # 文件里面必须具有有效的hosts配置，但是当通过动态生成的资产信息的时候这个文件必须存在但是它里面可以是空的，如果这里配置成None那么
        # 它不影响资产信息动态生成但是会有一个警告，所以还是要配置一个真实文件。

        self.inventory = inventory if inventory else "localhost,"

        # 实例化数据解析器
        self.loader = DataLoader()

        # 设置密码
        self.passwords = dict(conn_pass=remote_password)

        # 实例化回调插件对象
        self.results_callback = ResultCallback()

        # 实例化 资产配置对象
        # self.inv_obj = InventoryManager(loader=self.loader, sources="localhost,")

        # 动态配置 Inventory
        MyInventory(hostsresource)
        myinven = MyInventory(hostsresource=hostsresource)
        self.inv_obj = myinven.INVENTORY
        # inv_host = self.inv_obj.get_host('39.104.83.140')
        # print(inv_host.get_vars())
        # 变量管理器
        self.variable_manager = VariableManager(self.loader, self.inv_obj)

    def run(self, hosts='localhost', gether_facts="no", module="ping", args='', task_time=0):
        """
        参数说明：
        task_time -- 执行异步任务时等待的秒数，这个需要大于 0 ，等于 0 的时候不支持异步（默认值）。这个值应该等于执行任务实际耗时时间为好
        """
        play_source = dict(
            name="Ad-hoc",
            hosts=hosts,
            gather_facts=gether_facts,
            tasks=[
                # 这里每个 task 就是这个列表中的一个元素，格式是嵌套的字典
                # 也可以作为参数传递过来，这里就简单化了。
                {"action": {"module": module, "args": args}, "async": task_time, "poll": 0}])

        play = Play().load(play_source, variable_manager=self.variable_manager, loader=self.loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                inventory=self.inv_obj,
                variable_manager=self.variable_manager,
                loader=self.loader,
                passwords=self.passwords,
                stdout_callback=self.results_callback)

            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()
            shutil.rmtree(C.DEFAULT_LOCAL_TMP, True)

    def playbook(self, playbooks):
        """
        Keyword arguments:
        playbooks --  需要是一个列表类型
        """
        from ansible.executor.playbook_executor import PlaybookExecutor

        playbook = PlaybookExecutor(playbooks=playbooks,
                                    inventory=self.inv_obj,
                                    variable_manager=self.variable_manager,
                                    loader=self.loader,
                                    passwords=self.passwords)

        # 使用回调函数
        playbook._tqm._stdout_callback = self.results_callback

        result = playbook.run()

    def get_result(self):
        result_raw = {'success': {}, 'failed': {}, 'unreachable': {}}

        # print(self.results_callback.host_ok)
        for host, result in self.results_callback.host_ok.items():
            result_raw['success'][host] = result._result
        for host, result in self.results_callback.host_failed.items():
            result_raw['failed'][host] = result._result
        for host, result in self.results_callback.host_unreachable.items():
            result_raw['unreachable'][host] = result._result

        # 最终打印结果，并且使用 JSON 继续格式化
        print(json.dumps(result_raw, indent=4))

        return json.dumps(result_raw)


class MyInventory:
    def __init__(self, hostsresource):
        """
        初始化函数
        :param hostsresource: 主机资源可以有2种形式
        列表形式: [{"ip": "172.16.48.171", "port": "22", "username": "root", "password": "123456"}]
        字典形式: {
                    "Group1": {
                        "hosts": [{"ip": "192.168.200.10", "port": "1314", "username": "root", "password": None}],
                        "vars": {"var1": "ansible"}
                    },
                    "Group2": {}
                }
        """
        self._hostsresource = hostsresource
        self._loader = DataLoader()
        # self._hostsfilelist = ["temphosts"]
        """
        sources这个我们知道这里是设置hosts文件的地方，它可以是一个列表里面包含多个文件路径且文件真实存在，在单纯的执行ad-hoc的时候这里的
        文件里面必须具有有效的hosts配置，但是当通过动态生成的资产信息的时候这个文件必须存在但是它里面可以是空的，如果这里配置成None那么
        它不影响资产信息动态生成但是会有一个警告，所以还是要配置一个真实文件。
        """

        self._inventory = InventoryManager(loader=self._loader, sources="localhost,")
        # self._variable_manager = VariableManager(loader=self._loader, inventory=self._inventory)

        self._dynamic_inventory()

    def _add_dynamic_group(self, hosts_list, groupname, groupvars=None):
        """
        动态添加主机到指定的主机组

        完整的HOSTS文件格式
        [test1]
        hostname ansible_ssh_host=192.168.1.111 ansible_ssh_user="root" ansible_ssh_pass="123456"

        但通常我们都省略hostname，端口也省略因为默认是22，这个在ansible配置文件中有，除非有非22端口的才会配置
        [test1]
        192.168.100.10 ansible_ssh_user="root" ansible_ssh_pass="123456" ansible_python_interpreter="/PATH/python3/bin/python3"

        :param hosts_list: 主机列表 [{"ip": "192.168.100.10", "port": "22", "username": "root", "password": None}, {}]
        :param groupname:  组名称
        :param groupvars:  组变量，格式为字典
        :return:
        """
        # 添加组
        my_group = Group(name=groupname)
        self._inventory.add_group(groupname)

        # 添加组变量
        if groupvars:
            for key, value in groupvars.items():
                my_group.set_variable(key, value)

        # 添加一个主机
        for host in hosts_list:
            hostname = host.get("hostname", None)
            hostip = host.get("ip", None)
            if hostip is None:
                print("IP地址为空，跳过该元素。")
                continue
            hostport = host.get("port", "22")
            username = host.get("username", "root")
            password = host.get("password", None)
            ssh_key = host.get("ssh_key", None)
            python_interpreter = host.get("python_interpreter", None)

            try:
                # hostname可以不写，如果为空默认就是IP地址
                if hostname is None:
                    hostname = hostip

                # 添加主机到组
                self._inventory.add_host(host=hostname, group=groupname, port=hostport)
                inv_host = self._inventory.get_host(hostname)

                # 添加主机变量
                inv_host.set_variable('ansible_ssh_host', hostip)
                inv_host.set_variable('ansible_ssh_port', hostport)
                inv_host.set_variable('ansible_ssh_user', username)
                if password:
                    inv_host.set_variable('ansible_ssh_pass', password)
                if ssh_key:
                    inv_host.set_variable('ansible_ssh_private_key_file', ssh_key)
                if python_interpreter:
                    inv_host.set_variable('ansible_python_interpreter', python_interpreter)

                # 添加其他变量
                for key, value in host.items():
                    if key not in ["ip", "hostname", "port", "username", "password", "ssh_key", "python_interpreter"]:
                        inv_host.set_variable(key, value)

            except Exception as err:
                print(err)

    def _dynamic_inventory(self):
        """
        添加 hosts 到inventory
        :return:
        """
        if isinstance(self._hostsresource, list):
            self._add_dynamic_group(self._hostsresource, "default_group")
        elif isinstance(self._hostsresource, dict):
            for groupname, hosts_and_vars in self._hostsresource.items():
                self._add_dynamic_group(hosts_and_vars.get("hosts"), groupname, hosts_and_vars.get("vars"))

    @property
    def INVENTORY(self):
        """
        返回资产实例
        :return:
        """
        return self._inventory

    # @property
    # def VARIABLE_MANAGER(self):
    #     """
    #     返回变量管理器实例
    #     :return:
    #     """
    #     return self._variable_manager


if __name__ == '__main__':
    hostsresource = [{"ip": "39.104.83.140", "port": "22", "username": "root", "password": "asdqwe123."}]
    temphosts_dict = {
        "test": {
            "hosts": [{"ip": "39.104.83.140", "port": "22", "username": "root", "password": "asdqwe123."}],
            "vars": {}
        }
    }

    asb = MyAnsiable2(connection='smart', hostsresource=temphosts_dict)
    # asb.run(hosts="test", module="shell", args='df -m')
    asb.run(hosts="test", module="ping", args='')

    stdout_dict = json.loads(asb.get_result())
    print(stdout_dict)

