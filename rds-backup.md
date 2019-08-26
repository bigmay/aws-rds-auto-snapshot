
<style type="text/css">img {border: 1px}</style>

# 1. RDS定时备份

- [1.1. 简介](#11-简介)
- [1.2. 手动部署](#12-手动部署)
- [1.3 自动部署](#13-自动部署)

## **1.1. 简介**

目前RDS的自动备份方法是在每日的固定时间进行备份，换言之备份频率为固定每日一次，若想要实现小时级或者分钟级的备份频率则无法通过这种方法来解决。因此，本文提供了一种解决方案：通过AWS CloudWatch Events定时任务触发AWS Lambda函数来执行备份RDS的操作。

本文提供了手动部署的流程以及相关lambda的代码。同样，本文还提供了一个CloudFormation自动化部署脚本。该脚本可以快速自动完成部署，不需要您修改任何代码相关的部分，但相比起手动创建来说会多创建2个标准参数 （AWS System Manager服务中的Parameter store服务，具体说明参见下文）。

## **1.2. 手动部署**

- ### **1、创建基础的Lambda**

    在Lambda创建界面，选择 **从头开始创作**，运行语言选择Python3.7。
    在 **权限 - 执行角色** 中选择 **创建具有基本Lambda权限的角色**

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/manual-create-lambda.png)

- ### **2、填入代码**

    - **RDS版参数说明及代码** 

    在该Lambda函数界面中，将以下代码粘贴进函数代码中，修改参数：
    
    - 第四行 MAX_SNAPSHOTS : 您想保存最大的副本数量(最大100)
    - 第五行 DB_INSTANCE_NAME ：您想应用该脚本的RDS实例名称, 或者一组名称
    
    然后选择右上角 **保存**。

```python
import boto3
import time
def lambda_handler(event, context):
    MAX_SNAPSHOTS = 5
    DB_INSTANCE_NAMES = ['test','test2']
    clientRDS = boto3.client('rds')
    for DB_INSTANCE_NAME in DB_INSTANCE_NAMES:
        db_snapshots = clientRDS.describe_db_snapshots(
            SnapshotType='manual',
            DBInstanceIdentifier= DB_INSTANCE_NAME
        )['DBSnapshots']
        for i in range(0, len(db_snapshots) - MAX_SNAPSHOTS + 1):
            oldest_snapshot = db_snapshots[0]
            for db_snapshot in db_snapshots:
                if oldest_snapshot['SnapshotCreateTime'] > db_snapshot['SnapshotCreateTime']:
                    oldest_snapshot = db_snapshot
            clientRDS.delete_db_snapshot(DBSnapshotIdentifier=oldest_snapshot['DBSnapshotIdentifier'])
            db_snapshots.remove(oldest_snapshot)
        clientRDS.create_db_snapshot(
            DBSnapshotIdentifier=DB_INSTANCE_NAME + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
            DBInstanceIdentifier=DB_INSTANCE_NAME
        )
```

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/save_code.png)

- ### **3、添加IAM Role权限**

    在下方 **执行界面** 中，点击 **查看your_iam_role角色** , 进入该角色的摘要中。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/iam_role.png)

    在 **摘要界面** 中，选择 **添加内联策略** ，按照下图选定指定规则，然后输入该内联策略名称后创建。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/iam_add_role.png)

    RDS脚本所需规则：

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/create_rules.png)
    


- ### **4、添加触发器**

    在该Lambda函数界面，选择 **添加触发器**。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/console_trigger.png)

    在 **触发器配置** 中，选择 **CloudWatch Events**，规则选择 **创建新规则** ，**规则类型** 选择 **计划表达式**，按规则填入(e.g. 每两小时则为**rate(2 hours)**, 详情参见[规则的计划表达式](https://docs.amazonaws.cn/AmazonCloudWatch/latest/events/ScheduledEvents.html))

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/input_trigger.png)


- ### **5、创建完成**

    至此全部手动部署工作已经全部完成。

## **1.3. 自动部署**

您可以通过点击下方 **Quick Start** 链接直接进入Cloudformation创建页面。该模板会自动创建上述手动部署流程中的各个资源，不需要您像手动部署一样修改lambda的代码。

[![Image link china](http://cdn.quickstart.org.cn/assets/ChinaRegion.png)](https://console.amazonaws.cn/cloudformation/home?region=cn-north-1#/stacks/new?stackName=backup-rds&templateURL=https://quickstart-rds-backup.s3.cn-north-1.amazonaws.com.cn/rds-backup.yaml)

### 流程要点

- 检查导航栏右上角显示的所在区域，根据需要进行更改。

- 在 **指定模板** 页面上，保留模板 URL 的默认设置，然后选择 **下一步** 。
![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/CFN_template.png)

- 在 **指定堆栈详细信息** 页面上，填写您的自定义参数，参数说明如下：

  - rdsInstanceName: 您想应用该脚本的RDS实例名称，或者一组名称，用逗号分隔（e.g. db1,db2,db3）
  - MaxSnapshotNumber: 您想保存最大的副本数量(最大100)

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/specifyInfo.png)

### **修改应用该脚本的RDS实例或者最大备份上限**

若您希望修改应用该脚本的RDS实例或者最大备份上限的话，操作如下：

- 进入服务 **AWS Systems Manager - Parameter Store**，编辑修改图中两参数的值。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/param_store.png)

    


### **自定义修改备份时间**

该脚本默认自动创建备份的时间为2小时。

若您希望对自动备份的时间进行自定义修改的话，具体操作如下：

- 在该cloudformation的 **资源** 选项中点击类型为 **AWS::Lambda::Function** 的实体ID链接，进入该lambda函数界面。

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/CFN_lambda.png)

- 在 **Designer** 界面中点击 **CloudWatch Events** 图标， 在下方出现的触发事件界面中点击该规则链接，进入 **事件规则** 页面。

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/cloudWatch_event.png)

- 在该事件规则界面中，选择右上角 **操作** 按钮，点击进入 **编辑** 页面。

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/edit_event.png)

- 在 **事件源** 界面中，您可以修改触发事件的固定频率，或者使用 [规则的计划表达式](https://docs.amazonaws.cn/AmazonCloudWatch/latest/events/ScheduledEvents.html)，完成后点击 **配置详细信息** 进入下一页面，然后点击 **保存修改** 。

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/edit_event2.png)
