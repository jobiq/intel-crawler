import subprocess
import asyncio

import yaml
from yaml import YAMLError
from api import db

from prisma import Json

from scrape import do_the_job
from scraper.queue import ScraperQueue
import os

async def list_scrapers():
    print("------------------------")
    prisma = await db.connect(True)
    scrapers = await prisma.scraper.find_many()
    if scrapers:
        print("Available scrapers:")
        for scraper in scrapers:
            print(f"{scraper.id}. {scraper.name}")
    else:
        print("No scrapers found.")
    await prisma.disconnect()

def open_yaml_file(file_path: str):
    try:
        with open("./definitions/" + file_path, 'r') as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"❌ File {file_path} not found.")
        return None
    except YAMLError as e:
        print(f"❌ Error parsing YAML file: {e}")
        return None

async def launch_scraper():
    while True:
        scraper_id = input("\nEnter the scraper ID to launch (or 'l' to list scrapers, 'q' to quit): ").strip()
        if scraper_id.lower() == 'q':
            return None
        elif scraper_id.lower() == 'l':
            await list_scrapers()
        else:
            prisma = await db.connect()
            scrapers = await prisma.scraper.find_many()

            try:
                scraper_id = int(scraper_id)
                if not any(scraper.id == scraper_id for scraper in scrapers):
                    print(f"No scraper found with ID {scraper_id}. Please try again.")
                    continue
                else:
                    break
            except ValueError:
                print("Invalid ID. Please enter a valid integer ID.")
                return None
        
    workers = input("Enter number of workers (default 1): ").strip()
    if not workers:
        workers = 1
    else:
        try:
            workers = int(workers)
        except ValueError:
            print("Invalid number of workers. Defaulting to 1.")
            workers = 1

    parameters = input("Enter parameters for the scraper (e.g., 'name=example, name=example'): ").strip()
    
    # turn parameters into dictionary
    params_dict = {}
    if parameters:
        for param in parameters.split(","):
            if "=" in param:
                key, value = param.split("=", 1)
                params_dict[key.strip()] = value.strip()
    
    queue = ScraperQueue(num_workers=workers)
    await do_the_job(params_dict, queue, [scraper_id])

async def edit_scraper():
    
    while True:
      scraper_id = input("Enter the scraper ID to edit (or 'new' to create new scraper, 'l' to list scrapers, 'q' to quit): ").strip()
      if scraper_id.lower() == 'q':
          return None
      elif scraper_id.lower() == 'l':
          await list_scrapers()
      elif scraper_id.lower() == 'new':
          scraper_id = -1
          break
      else:
          try:
              scraper_id = int(scraper_id)
              break
          except ValueError:
              print("❌ Invalid ID. Please enter a valid integer ID.")
              return None
        
    prisma = await db.connect()
    scrapers = await prisma.scraper.find_many()

    if scraper_id != -1 and not any(scraper.id == scraper_id for scraper in scrapers):
        print(f"❌ No scraper found with ID {scraper_id}. Please try again.")
        return None
    
    # Implement the logic to edit the scraper here
    yaml_files = [
      f for f in os.listdir("./definitions")
      if f.endswith(".yaml") and ".scraper" in f
    ]
    if yaml_files:
      print("\nAvailable scraper YAML files:")
      for idx, fname in enumerate(yaml_files, 1):
        print(f"{idx}. {fname}")
    else:
      print("❌ No scraper files with 'scraper-*.yaml' in the name found.")
      return
    
    while True:
      scraper_choice = input("\nEnter the number of the scraper file to edit (or 'q' to quit): ").strip()
      if scraper_choice.lower() == 'q':
          return None
      try:
          scraper_choice = int(scraper_choice) - 1
          if scraper_choice < 0 or scraper_choice >= len(yaml_files):
              print("❌ Invalid choice. Please try again.")
              return None
          else:
            break
      except ValueError:
          print("❌ Invalid input. Please enter a number.")
          return None
    
    scraper_path = yaml_files[scraper_choice]
    
    # parse yaml file
    scraper_data = open_yaml_file(scraper_path)
    if scraper_data is None:
        print("❌ Failed to load or parse the scraper file. Please check the file path and format.")
        return None
  
    scraper_content = open_yaml_file(scraper_data["source"])
    if scraper_content is None:
        print("❌ Failed to load or parse the scraper content file. Please check the file path and format.")
        return None
    
    if scraper_id == -1:
        await prisma.scraper.create(
            data={
                "name": scraper_data["name"],
                "source": yaml.dump(scraper_content, default_flow_style=False),
                "active": True,
                "logo": scraper_data["logo"],
                "propertySchema": Json(scraper_data.get("propertySchema", {})),
                "schedule": Json(scraper_data.get("schedule", {})),
                "type": scraper_data.get("type", "default"),
                "url": scraper_data.get("url", ""),
            }
        )
    else:
        await prisma.scraper.update(
            where={"id": scraper_id},
            data={
                "name": scraper_data["name"],
                "source": yaml.dump(scraper_content, default_flow_style=False),
                "active": True,
                "logo": scraper_data["logo"],
                "propertySchema": Json(scraper_data.get("propertySchema", {})),
                "schedule": Json(scraper_data.get("schedule", {})),
                "type": scraper_data.get("type", "default"),
                "url": scraper_data.get("url", ""),
            }
        )

    print(f"✅ Scraper {'created' if scraper_id == -1 else 'updated'} successfully.")



def main():
    while True:
        print("\n--------------------------")
        print("JobIQ Data Manager Backend")
        print("--------------------------")
        print("Select an option:")
        print("1. Launch server")
        print("2. Start scraper")
        print("3. Edit scraper")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "0":
            print("Exiting.")
            break
        if choice == "1":
            print("Launching server...")
            subprocess.run(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"])
        elif choice == "2":
            asyncio.run(launch_scraper())
        elif choice == "3":
            asyncio.run(edit_scraper())
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()