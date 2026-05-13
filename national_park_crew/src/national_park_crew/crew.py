from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import WebsiteSearchTool, ScrapeWebsiteTool
from typing import List

@CrewBase
class NationalParkCrew:
    """NationalParkCrew crew"""
    BOOKING_URL = "https://www.booking.com/"
    agents: List[BaseAgent]
    tasks: List[Task]

    general_web_tool = WebsiteSearchTool()
    general_scrape_tool = ScrapeWebsiteTool()

    national_park_web_tool = WebsiteSearchTool(
        name="National Park Researcher",
        description="Search for information about national parks",
        url="https://www.nps.gov/index.htm"
    )

    national_park_scrape_tool = ScrapeWebsiteTool(
        name="National Park Scraper",
        description="Scrape information about national parks",
        url="https://www.nps.gov/index.htm"
    )

    accommodations_web_tool = WebsiteSearchTool(
        name="Accommodations Researcher",
        description="Search for information about hotels, motels, resorts, rentals and more in the US.",
        url=BOOKING_URL
    )

    accommodations_scrape_tool = ScrapeWebsiteTool(
        name="Accommodations Scraper",
        description="Scrape information about hotels, motels, resorts, rentals and more in the US.",
        url=BOOKING_URL
    )

    flight_web_tool = WebsiteSearchTool(
        name="Flight Researcher",
        description="Search for information about flights",
        url="https://www.google.com/travel/flights"
    )

    flight_scrape_tool = ScrapeWebsiteTool(
        name="Flight Scraper",
        description="Scrape information about flights",
        url="https://www.google.com/travel/flights"
    )

    @agent
    def general_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['general_researcher'], # type: ignore[index]
            verbose=True,
            tools=[self.general_web_tool]
        )

    @agent
    def flight_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['flight_researcher'], # type: ignore[index]
            verbose=True,
            tools=[self.flight_web_tool, self.general_web_tool, self.flight_scrape_tool]
        )

    @agent
    def accommodation_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['accommodation_researcher'],  # type: ignore[index]
            verbose=True,
            tools=[self.accommodations_web_tool, self.general_web_tool, self.accommodations_scrape_tool]
        )

    @agent
    def national_park_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['national_park_researcher'],  # type: ignore[index]
            verbose=True,
            tools=[self.national_park_web_tool, self.general_web_tool, self.national_park_scrape_tool]
        )

    @agent
    def reporting_writer(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_writer'],  # type: ignore[index]
            verbose=True
        )

    @task
    def general_research_task(self) -> Task:
        return Task(
            config=self.tasks_config['general_research_task'], # type: ignore[index]
        )

    @task
    def flight_researcher_task(self) -> Task:
        return Task(
            config=self.tasks_config['flight_researcher_task'], # type: ignore[index]
        )

    @task
    def accommodation_researcher_task(self) -> Task:
        return Task(
            config=self.tasks_config['accommodation_researcher_task'],  # type: ignore[index]
        )

    @task
    def national_park_researcher_task(self) -> Task:
        return Task(
            config=self.tasks_config['national_park_researcher_task'],  # type: ignore[index]
        )

    @task
    def reporting_writer_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_writer_task'],  # type: ignore[index]
        )

    @crew
    def crew(self) -> Crew:
        """Creates the NationalParkCrew crew"""
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you want to use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
