import asyncio
import json
from urllib.parse import quote
import aiohttp
import os


class TitlePage:
    def __init__(self, id, title, created, updated):
        self.id = id
        self.title = title
        self.created = created
        self.updated = updated


project = "villagepump"
dist_stats = f"./{project}/stats/pages.json"
dist_data = "./data.json"


async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()


async def main():
    pages_response = await fetch(f"https://scrapbox.io/api/pages/{project}/?limit=1")
    page_num = pages_response["count"]
    limit_param = 1000
    max_index = (page_num // 1000) + 1

    pages = []
    tasks = [fetch(
        f"https://scrapbox.io/api/pages/{project}/?limit={limit_param}&skip={index * 1000}") for index in range(max_index)]
    for task in asyncio.as_completed(tasks):
        result = await task
        pages.extend(result["pages"])

    titles = [TitlePage(page["id"], page["title"],
                        page["created"], page["updated"]) for page in pages]
    titles.sort(key=lambda x: x.created)

    write_json(dist_stats, {
        "projectName": project,
        "count": page_num,
        "pages": [title.__dict__ for title in titles]
    })

    skip = 100
    detail_pages = []
    for i in range(0, len(titles), skip):
        print(
            f"[scrapbox-external-backup] Start fetching {i} - {i + skip} pages.")
        tasks = [fetch(
            f"https://scrapbox.io/api/pages/{project}/{quote(title.title)}") for title in titles[i:i+skip]]
        for j, task in enumerate(asyncio.as_completed(tasks), start=i):
            print(
                f"[page {j}@scrapbox-external-backup] start fetching /{project}/{titles[j].title}")
            result = await task
            print(
                f"[page {j}@scrapbox-external-backup] finish fetching /{project}/{titles[j].title}")
            detail_pages.append({
                "id": result["id"],
                "title": result["title"],
                "created": result["created"],
                "updated": result["updated"],
                "lines": result["lines"]
            })
        print(f"Finish fetching {i} - {i + skip} pages.")

    with open(dist_data, "w") as file:
        for page in detail_pages:
            file.write(json.dumps(page) + ",\n")
        print("write success")


def write_json(path, data):
    try:
        with open(path, "w") as file:
            json.dump(data, file)
        return "Written to " + path
    except Exception as e:
        return str(e)


asyncio.run(main())
