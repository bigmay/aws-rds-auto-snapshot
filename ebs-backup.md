

# EBS定时备份

[返回首页](https://github.com/fanyizhe/aws-auto-snapshot)

- [1. 简介](#1-简介)
- [2. 手动部署](#2-手动部署)
- [3. 自动部署](#3-自动部署)

## **1. 简介**

目前EBS中国区暂无定时自动创建EBS快照的功能。因此，本文提供了一种解决方案：通过AWS CloudWatch Events定时任务触发AWS Lambda函数来执行备份EBS的操作。

本文提供了手动部署的流程以及相关lambda的代码, 您可以按照该流程一步步创建所需资源。 同样，本文还提供了一个CloudFormation自动化部署脚本。该脚本可以快速自动完成部署，不需要您修改任何代码相关的部分。

## **2. 手动部署**

- ### **2.1. 创建基础的Lambda**

    在Lambda创建界面，选择 **从头开始创作**，运行语言选择Python3.7。
    在 **权限 - 执行角色** 中选择 **创建具有基本Lambda权限的角色**

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/manual-create-lambda.png)

- ### **2.2. 填入代码**

    在该Lambda函数界面中，将以下代码粘贴进函数代码中，修改参数：
    
    - 第四行 MAX_SNAPSHOTS : 您想保存最大的副本数量(最大100)
    - 第五行 EBS_VOLUME_IDS ：您想应用该脚本的EBS卷名称（e.g. 'vol-xxxxxx'）, 或者一组名称
    
    然后选择右上角 **保存**。

```python
import boto3
import time
def lambda_handler(event, context):
    MAX_SNAPSHOTS = 5
    EBS_VOLUME_IDS = ['vol-xxxxxx']
    clientEC2 = boto3.client('ec2')
    for EBS_VOLUME_ID in EBS_VOLUME_IDS:
        ebs_snapshots = clientEC2.describe_snapshots(
            Filters=[
                {
                    'Name': 'volume-id',
                    'Values': [EBS_VOLUME_ID]
                },
            ],
        )['Snapshots']
        for i in range(0, len(ebs_snapshots) - MAX_SNAPSHOTS + 1):
            oldest_snapshot = ebs_snapshots[0]
            for ebs_snapshot in ebs_snapshots:
                if oldest_snapshot['StartTime'] > ebs_snapshot['StartTime']:
                    oldest_snapshot = ebs_snapshot
            clientEC2.delete_snapshot(SnapshotId=oldest_snapshot['SnapshotId'])
            ebs_snapshots.remove(oldest_snapshot)
        clientEC2.create_snapshot(
            Description=EBS_VOLUME_ID + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime()),
            VolumeId=EBS_VOLUME_ID
        )

```

- ### **2.3. 添加IAM Role权限**

    在下方 **执行界面** 中，点击 **查看your_iam_role角色** , 进入该角色的摘要中。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/iam_role.png)

    在 **摘要界面** 中，选择 **添加内联策略** ，按照下图选定指定规则，然后输入该内联策略名称后创建。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/iam_add_role.png)

    ![EBS脚本规则](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/ebs/ebs_add_iam_role.png)


- ### **2.4. 添加触发器**

    在该Lambda函数界面，选择 **添加触发器**。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/console_trigger.png)

    在 **触发器配置** 中，选择 **CloudWatch Events**，规则选择 **创建新规则** ，**规则类型** 选择 **计划表达式**，按规则填入(e.g. 每两小时则为**rate(2 hours)**, 详情参见[规则的计划表达式](https://docs.amazonaws.cn/AmazonCloudWatch/latest/events/ScheduledEvents.html))
    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/input_trigger.png)


- ### **2.5. 创建完成**

    至此全部手动部署工作已经全部完成。

## **3. 自动部署**

您可以通过点击下方 **Quick Start** 链接直接进入创建页面, 该模板会自动创建上述手动部署流程中的各个资源。

[![Image link china](http://cdn.quickstart.org.cn/assets/ChinaRegion.png)](https://console.amazonaws.cn/cloudformation/home?region=cn-north-1#/stacks/new?stackName=backup-ebs&templateURL=https://quickstart-rds-backup.s3.cn-north-1.amazonaws.com.cn/ebs-backup.yaml)



### 3.1. **部署要点**

- 检查导航栏右上角显示的所在区域，根据需要进行更改。

- 在 **指定模板** 页面上，保留模板 URL 的默认设置，然后选择 **下一步** 。
![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/CFN_template.png)

- 在 **指定堆栈详细信息** 页面上，填写堆栈名称以及您自定义参数，完成后选择 **下一步**

    - EBSVolumeId: 您想应用该脚本的EBS卷名称，或者一组名称，用逗号分隔(e.g. vol-1,vol-2,vol-3)
    - MaxSnapshotNumber: 您想保存最大的副本数量(最大100)

    **注意** ：在此您已自定义了相关参数，因此之后无需在lambda的代码界面修改相应代码。若您希望在资源创建后再次修改，请参考下文 **修改应用该脚本的EBS实例或者最大备份上限**



### **3.2. 修改应用该脚本的EBS实例或者最大备份上限**

若您希望修改应用该脚本的EBS实例或者最大备份上限的话，操作如下：

- 进入服务 **AWS Systems Manager - Parameter Store**，编辑修改图中两参数的值。

    ![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/ebs/ebs_change_param.png)


### **3.3. 自定义修改备份时间**

该脚本默认自动创建备份的时间为2小时。

若您希望对自动备份的时间进行自定义修改的话，具体操作如下：

- 在该Lambda函数的 **Designer** 界面中点击 **CloudWatch Events** 图标， 在下方出现的触发事件界面中点击该规则链接，进入 **事件规则** 页面。
![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/cloudWatch_event.png)

- 在该事件规则界面中，选择右上角 **操作** 按钮，点击进入 **编辑** 页面。
- 在 **事件源** 界面中，您可以修改触发事件的固定频率，或者使用 [规则的计划表达式](https://docs.amazonaws.cn/AmazonCloudWatch/latest/events/ScheduledEvents.html)，完成后点击 **配置详细信息** 进入下一页面，然后点击 **保存修改** 。
![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/edit_event2.png)
