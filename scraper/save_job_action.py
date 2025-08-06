from typing import Any

from api.db import connect
from scraper.helpers import current_date
from scraper.action import ScraperAction, ScraperItem
from prisma.enums import  SalaryPeriod

class SaveJob(ScraperAction[Any]):
    uid = "jobiq.save_job"

    async def init(self):
        self.prisma = await connect()

    async def _execute(self, scraper: ScraperItem):
        item = scraper.item

        if "employer" in item:
            employer = await self.prisma.employer.find_first(
                where={"name": item["employer"]} 
            )
            if employer is None:
                employer = await self.prisma.employer.create(data={
                    "name": item["employer"],
                    "webId": "",
                    "scraperId": scraper.context.scraper.id,
                })
            employer_id = employer.id
        else:
            employer_id = 0

        await self.prisma.job.create(data={
            "city": item["city"] if "city" in item else None,
            "country": item["country"] if "country" in item else None,
            "createdDate": item["createdDate"] if "createdDate" in item else None,
            # "domain": None,
            # "domainId": None,
            "expiryDate": item["expiryDate"] if "expiryDate" in item else None,
            "logo": item["logo"] if "logo" in item and item["logo"] != None else "",
            "employerId": employer_id,
            "intermediary": item["intermediary"] if "intermediary" in item else None,
            "industryId": 0,
            "jobId": str(item["jobId"]),
            # "jobType": item["jobType"] if "jobType" in item else None,
            "postCode": item["postCode"] if "postCode" in item else "",
            # "industryCode": item["industryCode"] if "industryCode" in item else "",
            # "maxExperience": Optional[float]
            "minSalary": item["maxAnnualSalary"] if "maxAnnualSalary" in item else
                         item["minMonthlySalary"] if "minMonthlySalary" in item else
                         item["minHourlySalary"] if "minHourlySalary" in item else
                         None,
            "maxSalary": item["maxAnnualSalary"] if "maxAnnualSalary" in item else
                            item["maxMonthlySalary"] if "maxMonthlySalary" in item else
                            item["maxHourlySalary"] if "maxHourlySalary" in item else
                            None,
            "salaryPeriod": SalaryPeriod.YEAR if "maxAnnualSalary" in item else
                            SalaryPeriod.MONTH if "maxMonthlySalary" in item else 
                            SalaryPeriod.HOUR if "maxHourlySalary" in item else 
                            None,
            "salaryCurrency": item["salaryCurrency"] if "salaryCurrency" in item else None,
            "education": item["education"] if "education" in item else None,
            "minExperience": item["minExperience"] if "minExperience" in item else None,
            "region": item["region"] if "region" in item else None,
            # "requiredDegrees": Optional[str]
            "state": item["state"] if "state" in item else None,
            "text": item["description"] if "description" in item else item["text"] if "text" in item else "",
            "title": item["title"] if "title" in item else "",
            "url": scraper.url,
            # "Skills": {"create": item["Skills"]["Skills"]},
            # "Roles": {"create": item["Skills"]["Role"]},
            "scraperId": scraper.context.scraper.id,
            "scrapedDate": current_date()
        })

        scraper.context.succeeded += 1
