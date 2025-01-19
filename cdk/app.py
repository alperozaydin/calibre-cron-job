from aws_cdk import (
    aws_ec2,
    aws_ecs,
    aws_ecr,
    aws_events,
    aws_events_targets,
    aws_logs,
    App,
    Stack
)

class FargateCronJobStack(Stack):

    def __init__(self, scope: App, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        vpc = aws_ec2.Vpc(self, "FargateVpc",
            max_azs=2,
            nat_gateways=1
        )

        cluster = aws_ecs.Cluster(self, "FargateCluster",
            vpc=vpc
        )

        repository = aws_ecr.Repository.from_repository_name(self, "CalibreRepo", "calibre-cron-job")

        log_group = aws_logs.LogGroup(self, "CalibreCronLogGroup",
            retention=aws_logs.RetentionDays.ONE_WEEK
        )

        task_definition = aws_ecs.FargateTaskDefinition(self, "CalibreTask",
            cpu=256,
            memory_limit_mib=512,
            runtime_platform=aws_ecs.RuntimePlatform(
                operating_system_family=aws_ecs.OperatingSystemFamily.LINUX,
                cpu_architecture=aws_ecs.CpuArchitecture.ARM64
            )
        )

        task_definition.add_container("CalibreContainer",
            image=aws_ecs.ContainerImage.from_ecr_repository(repository, tag="latest"),
            logging=aws_ecs.LogDriver.aws_logs(
                stream_prefix="CalibreCronJob",
                log_group=log_group
            )
        )

        rule = aws_events.Rule(self, "CalibreCronRule",
            schedule=aws_events.Schedule.cron(minute="0", hour="7", week_day="FRI"),
        )

        ecs_task_target = aws_events_targets.EcsTask(
            cluster=cluster,
            task_definition=task_definition,
            subnet_selection=aws_ec2.SubnetSelection(subnet_type=aws_ec2.SubnetType.PUBLIC),
            task_count=1
        )

        rule.add_target(ecs_task_target)


app = App()
FargateCronJobStack(app, "FargateCronJobStack")
app.synth()
