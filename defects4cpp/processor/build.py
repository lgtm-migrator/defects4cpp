from typing import List, Optional

import message
from processor.core.argparser import create_common_project_parser, read_config
from processor.core.command import DockerCommand, DockerCommandScript, DockerExecInfo


class BuildCommandScript(DockerCommandScript):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def before(self, info: DockerExecInfo):
        pass

    def output(self, exit_code: int, stream: str):
        pass

    def after(
        self,
        info: "DockerExecInfo",
        exit_code: Optional[int] = None,
        output: Optional[str] = None,
    ):
        pass


class BuildCommand(DockerCommand):
    """
    Run build command either with or without coverage.
    """

    def __init__(self):
        super().__init__()
        self.parser = create_common_project_parser()
        self.parser.usage = "d++ build --project=[project_name] --no=[number] [--coverage] [checkout directory]"

    def run(self, argv: List[str]) -> DockerExecInfo:
        args = self.parser.parse_args(argv)
        metadata, worktree = read_config(args.path)

        commands = (
            [BuildCommandScript(metadata.common.build_coverage_command)]
            if args.coverage
            else [BuildCommandScript(metadata.common.build_command)]
        )
        stream = True if args.verbose else False

        return DockerExecInfo(metadata, worktree, commands, stream)

    def setup(self, info: DockerExecInfo):
        message.info(f"Building {info.metadata.name}")

    def teardown(self, info: DockerExecInfo):
        pass

    @property
    def help(self) -> str:
        return "Build local with a build tool from docker"
