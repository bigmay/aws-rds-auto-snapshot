
# EBS, RDS定时备份

[TOC]<!-- TOC -->autoauto- [EBS, RDS定时备份](#ebs-rds定时备份)auto    - [应用场景](#应用场景)auto    - [解决方案](#解决方案)auto        - [手动部署](#手动部署)auto        - [自动部署](#自动部署)autoauto<!-- /TOC -->

## 应用场景

目前RDS的自动备份方法是在每日的固定时间进行备份，换言之备份频率为固定每日一次，若想要实现小时级或者分钟级的备份频率则无法通过这种方法来解决。因此，本文提供了一种解决方案：通过AWS CloudWatch Events定时任务触发AWS Lambda函数来执行备份RDS的操作。

同样EBS也缺乏相应的备份解决方案，而它同样也能通过上述的解决方案来解决。

本文提供了手动部署的流程以及相关lambda的代码。同样，本文还提供了一个CloudFormation自动化部署脚本。该脚本可以快速自动完成部署，但相比起手动创建来说会多创建2个标准参数 （AWS System Manager服务中的Parameter store服务，具体说明参见下文）。

下文主要介绍以RDS的对象的解决方案。因为EBS的部署流程与RDS的基本相同，所以完全可以参考下文来进行部署，其中一些EBS与RDS部署的不同之处会加以说明。

## 解决方案

### 手动部署

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/rds-backup.png)

**创建的资源：**

- [CloudWatch Events](https://docs.aws.amazon.com/zh_cn/AmazonCloudWatch/latest/events/WhatIsCloudWatchEvents.html) ：使用 CloudWatch Events 来计划使用 cron 或 rate 表达式在某些时间自行触发的自动化操作。

- [Lambda](https://docs.aws.amazon.com/zh_cn/lambda/latest/dg/welcome.html) : 计算服务，可使您无需预配置或管理服务器即可运行代码。

- [IAM Role](https://docs.aws.amazon.com/zh_cn/IAM/latest/UserGuide/id_roles_terms-and-concepts.html) : IAM 角色类似于 IAM 用户，因为它是一个 AWS 身份，该身份具有确定其在 AWS 中可执行和不可执行的操作的权限策略。

### 自动部署

![](https://raw.githubusercontent.com/fanyizhe/aws-rds-auto-snapshot/dev/pic/rds-backup-auto.png)

相比手动部署，自动部署多运用了Parameter Store服务创建了两个参数，用以在CloudFormation脚本的创建过程中，向Lambda中指定所需的参数。

- [Parameter store](https://docs.aws.amazon.com/zh_cn/systems-manager/latest/userguide/systems-manager-parameter-store.html) : 将 Parameter Store 参数与其他 Systems Manager 功能和 AWS 服务配合使用，以从中央存储检索密钥和配置数据。  



