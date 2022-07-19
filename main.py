import discord
from discord import Interaction, app_commands
from discord.ext import commands, tasks
from discord.app_commands import Choice
import os
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
import asyncio
from functools import wraps, partial

class aclient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all())
        self.synced = False
    
    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild = discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"]))
            self.synced = True
        print(f"{self.user} has successfully connected to Discord.")

client = aclient()
tree = app_commands.CommandTree(client)

# GLOBAL VARIABLES
id_list = []
cwd = os.getcwd()

@tree.command(guild = discord.Object(id=os.environ["DEVELOPMENT_SERVER_ID"]), name="dallenew", description="Generate images from a prompt using Dalle AI")
async def dalle(interaction: discord.Interaction, prompt: str, artist: Optional[str] = None, style: Optional[str] = None) -> None:
    global id_list, cwd

    if interaction.user.id in id_list:
        embed = discord.Embed(title="Please wait for your current DALL-E image to complete", color=discord.Color.from_rgb(255, 0, 0))
        return await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        if artist is not None:
            prompt += f", by {artist}"
        if style is not None:
            prompt += f", in the style of {style}"
        id_list.append(interaction.user.id)
        await execute_dalle(interaction, prompt)

async def execute_dalle(interaction: discord.Interaction, prompt: str):
    global id_list, cwd
    loading_emoji = client.get_emoji(997263536076107827)

    #cloudinary account details for uploading images
    cloudinary.config( 
        cloud_name = os.environ["CLOUD_NAME"], 
        api_key = os.environ["API_KEY"], 
        api_secret = os.environ["API_SECRET"] 
    )

    # Send embeded message to discord stating the image generation has started
    embed = discord.Embed(title=f"Generating DALL-E Image now! {loading_emoji}", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
    embed.set_thumbnail(url="https://www.craiyon.com/_app/immutable/assets/craiyon_logo-9927047c.png")
    embed.set_footer(text="Please allow for up to 3 minutes.")
    await interaction.response.defer()
    # Get last sent message id so we can edit/delete when generation complete
    msg = await interaction.followup.send(embed=embed)

    # Generate unique image name based on author of command
    image_name = f"Dalle_Image_{interaction.user.id}_{str(uuid.uuid4().hex)}.png"

    await  wait_for_loading(prompt)

    # Find downloaded image in download folder, change name, upload to cloud website while saving it's URL and removing from downloads
    for i in  os.listdir(cwd):
        if i.startswith("craiyon_"):
            print(i)
            os.rename(f"{cwd}/{i}", f"{cwd}/{image_name}")
            image_url = cloudinary.uploader.upload_image(f"{cwd}/{image_name}", folder="Dalle Images/", use_filename = True).url
            os.remove(f"{cwd}/{image_name}")

    # Send embeded discord message with the generated IMG's URL 
    embed = discord.Embed(title=f"{interaction.user.name}'s Dalle Search Finished!", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
    embed.set_footer(text="Website Link: https://www.craiyon.com")
    embed.set_image(url=image_url)
    await interaction.followup.send(embed=embed)
    id_list.remove(interaction.user.id)
    embed = discord.Embed(title="Images Generated", color=discord.Color.from_rgb(255, 255, 255))
    await msg.edit(embed=embed)

# Wrap sync function in async decorator to run concurrently
def wrap(func):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)
    return run

# Use decorator to wrap long-running blocking code
@wrap
def wait_for_loading(prompt):
    global id_list, cwd
    #Dalle Information
    LOADING_ELEMENT = "//*[contains(text(), 'This should not take long (up to 2 minutes)...')]"
    SCREENSHOT_BUTTON = "//*[contains(text(), 'Screenshot')]"
    INPUT_FIELD = "prompt"
    RUN_BUTTON = '//*[@id="app"]/div/div/div[1]/button'
    POPUP_REJECT_ALL = "/html/body/div[1]/div/div/div/div[2]/div/button[2]"
    VIDEO_POPUP_EXIT = "//*[@id='av-close-btn']"

    #apply options to browser. Not currently used as headless causes program to crash
    #standard options work fine but window pops up when command runs
    chrome_options = webdriver.ChromeOptions()
    prefs = {'download.default_directory' : f"{cwd}"}
    chrome_options.add_experimental_option('prefs', prefs)
    chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), options=chrome_options)

    #navigate to dalle page
    driver.get("https://www.craiyon.com/")

    try:
        element = WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, POPUP_REJECT_ALL)))
        print("Popup found")
        driver.execute_script("arguments[0].click();", element)
        print("Popup rejected")
    except TimeoutException:
        print("Couldnt find popup menu in time")
    except ElementClickInterceptedException:
        print("Could not click reject on popup menu")
    except ElementNotInteractableException:
        print("Found element but could not click")
    
    #find website input box and type in prompt
    driver.find_element(By.ID, "prompt").send_keys(prompt)
    print("Prompt entered")
    #find website submit button and click
    element = driver.find_element(By.XPATH, RUN_BUTTON)
    print("Found run button")
    driver.execute_script("arguments[0].click();", element)
    print("Clicked run")

    # Loading element precense is checked to ensure generation has started.
    try:
        WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, LOADING_ELEMENT)))
        print("Loading element found.")

        # When loading element disappears we know generation has completed
        WebDriverWait(driver, 180).until_not(ec.presence_of_element_located((By.XPATH, LOADING_ELEMENT)))
        print("Loading stopped.")
    except TimeoutException:
        return print("Could not find loading element in time.")
    except ElementClickInterceptedException:
        return print("Element Click Intercepted Exception Raised.")
    except UnexpectedAlertPresentException:
        return print("Unexpected Alart Present")

    try:
        element = WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, VIDEO_POPUP_EXIT)))
        print("Video popup found element found.")
        driver.execute_script("arguments[0].click();", element)
        print("Video popup closed")
    except TimeoutException:
        print("could not find video popup")
    except ElementClickInterceptedException:
        print("Element Click Intercepted Exception Raised. POPUP VIDEO")
    except UnexpectedAlertPresentException:
        print("Unexpected Alert Present")

    try:
        element = WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, SCREENSHOT_BUTTON)))
        driver.execute_script("arguments[0].click();", element)
        asyncio.sleep(3)
        print("Screenshot taken")
    except TimeoutException:
        print("could not find screenshot button")
    except ElementClickInterceptedException:
        print("Element Click Intercepted Exception Raised. POPUP VIDEO")
    except UnexpectedAlertPresentException:
        print("Unexpected Alert Present")

    # close driver
    driver.close()
    print("Driver closed. DALL-E img generation complete.")

client.run(os.environ["DISCORD_TOKEN"])
