# register actions
from typing import Any, Dict, Type

from scraper.action import ScraperAction
from scraper.controls.error_boundary import ErrorBoundaryAction
from scraper.controls.for_each_action import ForEachAction
from scraper.controls.if_action import IfAction
from scraper.controls.repeat_action import Repeat
# from scraper.config import ScraperActionConfig
from scraper.eval_action import EvalAction
from scraper.extraction.extract_json_fields_action import \
    ExtractJsonFieldsAction
from scraper.extraction.extract_soup_fields_action import \
    ExtractSoupFieldsAction
from scraper.extraction.extract_soup_groups_action import \
    ExtractSoupGroupsAction
from scraper.fix.clear_skills import ClearSkills
from scraper.fix.list_errors import ListErrorAction
from scraper.fix.mark_fixed import MarkFixed
from scraper.flag_processed_job_action import FlagProcessedJob
from scraper.graphql_query_action import GraphqlRequest
from scraper.log.log_action import LogAction
from scraper.log.log_progress_action import LogProgressAction
from scraper.log.log_step_action import LogStepAction
from scraper.multiprocessing.merge_processes_action import MergeProcess
from scraper.multiprocessing.start_process_action import StartProcess
from scraper.parse_skills_action import ParseSkills
from scraper.requests.request_json_action import RequestJsonAction
from scraper.requests.request_selenium_soup_action import \
    SeleniumRequest
from scraper.requests.request_soup_action import RequestSoup
from scraper.save_job_action import SaveJob
from scraper.selenium.click_action import SeleniumClick
from scraper.selenium.cloudflare_human import CloudflareHuman


class ScraperActionsRepository:
    def __init__(self):
        self.actions: Dict[str, Type[ScraperAction[Any]]] = {
            SaveJob.uid: SaveJob,
            FlagProcessedJob.uid: FlagProcessedJob,
            # AI Parsers
            ParseSkills.uid: ParseSkills,
            # Requests
            RequestSoup.uid: RequestSoup,
            GraphqlRequest.uid: GraphqlRequest,
            SeleniumRequest.uid: SeleniumRequest,
            # Logging
            LogAction.uid: LogAction,
            LogStepAction.uid: LogStepAction,
            LogProgressAction.uid: LogProgressAction,
            # Controls
            Repeat.uid: Repeat,
            ForEachAction.uid: ForEachAction,
            EvalAction.uid: EvalAction,
            IfAction.uid: IfAction,
            ErrorBoundaryAction.uid: ErrorBoundaryAction,
            # Extraction
            ExtractSoupFieldsAction.uid: ExtractSoupFieldsAction,
            ExtractSoupGroupsAction.uid: ExtractSoupGroupsAction,
            ExtractJsonFieldsAction.uid: ExtractJsonFieldsAction,
            RequestJsonAction.uid: RequestJsonAction, 
            # selenium
            SeleniumClick.uid: SeleniumClick,
            CloudflareHuman.uid: CloudflareHuman,
            # MultiProcessing
            StartProcess.uid: StartProcess,
            MergeProcess.uid: MergeProcess,
            # fix
            ListErrorAction.uid: ListErrorAction,
            MarkFixed.uid: MarkFixed,
            ClearSkills.uid: ClearSkills
        }

    def has(self, name: str) -> bool:
        return name in self.actions

    # async def create(self, name: str, config: ScraperActionConfig) -> ScraperAction[Any]:
    #     action = self.actions[name](config,  self.actions)

    #     await action.init()

    #     return action


repository = ScraperActionsRepository()
