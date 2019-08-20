# RDS定时备份

## 应用场景

目前RDS的自动备份方法是在每日的固定时间进行备份，换言之备份频率为固定每日一次，若想要实现小时级或者分钟级的备份频率则无法通过这种方法来解决。因此，本文提供了一种解决方案：通过AWS CloudWatch Events定时任务触发AWS Lambda函数来执行备份RDS的操作。

本文提供了手动部署的流程以及相关lambda的代码。同样，本文还提供了一个CloudFormation自动化部署脚本。该脚本可以快速自动完成部署，但相比起手动创建来说会多创建2个标准参数 （AWS System Manager服务中的Parameter store服务，具体说明参见下文）。

## 解决方案架构图



### 手动部署

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/rds-backup.png)

**创建的资源：**

- [CloudWatch Events](https://docs.aws.amazon.com/zh_cn/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) ：使用 CloudWatch Events 来计划使用 cron 或 rate 表达式在某些时间自行触发的自动化操作。

- [Lambda](https://docs.aws.amazon.com/zh_cn/lambda/latest/dg/welcome.html) : 计算服务，可使您无需预配置或管理服务器即可运行代码。

- [IAM Role](https://docs.aws.amazon.com/zh_cn/IAM/latest/UserGuide/id_roles_terms-and-concepts.html) : IAM 角色类似于 IAM 用户，因为它是一个 AWS 身份，该身份具有确定其在 AWS 中可执行和不可执行的操作的权限策略。

- [RDS](https://docs.aws.amazon.com/zh_cn/AmazonRDS/latest/UserGuide/Welcome.html) : 关系型数据库服务

### 自动部署

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/rds-backup-auto.png)

相比手动部署，自动部署多运用了Parameter Store服务创建了两个参数，用以在CloudFormation脚本的创建过程中，向Lambda中指定所需的参数。

- [Parameter store](https://docs.aws.amazon.com/zh_cn/systems-manager/latest/userguide/systems-manager-parameter-store.html) : 将 Parameter Store 参数与其他 Systems Manager 功能和 AWS 服务配合使用，以从中央存储检索密钥和配置数据。  


## 手动部署

- 1、创建基础的Lambda

    在Lambda创建界面，选择 **从头开始创作**，运行语言选择Python3.7。
    在 **权限 - 执行角色** 中选择 **创建具有基本Lambda权限的角色**

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/manual-create-lambda.png)

- 2、填入代码

    在该Lambda函数界面中，将以下代码粘贴进函数代码中，修改参数：
    
    - 第四行 MAX_SNAPSHOTS : 您想保存最大的副本数量(最大100)
    - 第五行 DB_INSTANCE_NAME ：您想应用该脚本的RDS实例名称
    
    然后选择右上角 **保存**。

    ```
    import boto3
    import time
    def lambda_handler(event, context):
        MAX_SNAPSHOTS = 5
        DB_INSTANCE_NAME = 'test'
        clientRDS = boto3.client('rds')
        db_snapshots = clientRDS.describe_db_snapshots(
            SnapshotType='manual',
        )['DBSnapshots']
        if len(db_snapshots) >= MAX_SNAPSHOTS:
            oldest_snapshot = db_snapshots[0]
            for db_snapshot in db_snapshots:
                if db_snapshots[0]['SnapshotCreateTime'] > db_snapshot['SnapshotCreateTime']:
                    oldest_snapshot = db_snapshot
            clientRDS.delete_db_snapshot(DBSnapshotIdentifier=oldest_snapshot['DBSnapshotIdentifier'])
        create_snapshot = clientRDS.create_db_snapshot(
            DBSnapshotIdentifier=DB_INSTANCE_NAME + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
            DBInstanceIdentifier=DB_INSTANCE_NAME
        )
    ```
    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/save_code.png)


- 3、添加IAM Role权限

    在下方 **执行界面** 中，点击 **查看your_iam_role角色** , 进入该角色的摘要中。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/iam_role.png)

    在 **摘要界面** 中，选择 **添加内联策略** ，按照下图选定指定规则，然后输入该内联策略名称后创建。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/iam_add_role.png)

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/create_rules.png)

- 4、添加触发器

    在该Lambda函数界面，选择 **添加触发器**。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/console_trigger.png)

    在 **触发器配置** 中，选择 **CloudWatch Events**，规则选择 **创建新规则** ，**规则类型** 选择 **计划表达式**，按规则填入(e.g. 每两小时则为**rate(2 hours)**, 详情参见[规则的计划表达式](https://docs.amazonaws.cn/AmazonCloudWatch/latest/events/ScheduledEvents.html))

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/input_trigger.png)


- 5、创建完成

    至此全部手动部署工作已经全部完成。

## 自动部署

您可以通过点击下方 **Quick Start** 链接直接进入创建页面。

[![Image link china](http://cdn.quickstart.org.cn/assets/ChinaRegion.png)](https://console.amazonaws.cn/cloudformation/home?region=cn-north-1#/stacks/new?stackName=backup-rds&templateURL=https://quickstart-rds-backup.s3.cn-north-1.amazonaws.com.cn/rds-backup.yaml) 


### 要点

- 检查导航栏右上角显示的所在区域，根据需要进行更改。

- 在 **指定模板** 页面上，保留模板 URL 的默认设置，然后选择 **下一步** 。
![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/CFN_template.png)

- 在 **指定堆栈详细信息** 页面上，填写堆栈名称、您想应用该脚本的RDS实例名称,以及您想保存最大的副本数量(最大100)，完成后选择 **下一步**

    - rdsInstanceName: 您想应用该脚本的RDS实例名称
    - MaxSnapshotNumber: 您想保存最大的副本数量(最大100)

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/specifyInfo.png)


### （可选）自定义修改备份时间

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
