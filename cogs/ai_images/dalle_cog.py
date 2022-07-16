import discord
from discord import Interaction, app_commands
from discord.ext import commands, tasks
from selenium import webdriver
#from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
import BrianBotConfig as config
import os
import uuid
import cloudinary
import cloudinary.uploader
import cloudinary.api
import asyncio
import time
from functools import wraps, partial

class dalle(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.id_list = []
    
    @app_commands.command(
        name="dalle",
        description="Generate images from a prompt using Dalle AI")
    
    async def dalle(self, interaction: discord.Interaction, prompt: str) -> None:
        if interaction.user.id in self.id_list:
            embed = discord.Embed(title="Please wait for your current DALL-E image to complete", color=discord.Color.from_rgb(255, 0, 0))
            return await interaction.response.send_message(embed=embed)
        else:
            self.id_list.append(interaction.user.id)
            await self.execute_dalle(interaction, prompt)
    
    async def execute_dalle(self, interaction: discord.Interaction, prompt: str):
        loading_emoji = self.bot.get_emoji(997263536076107827)

        #cloudinary account details for uploading images
        cloudinary.config( 
            cloud_name = "dezhokgqf", 
            api_key = "938882534535316", 
            api_secret = "0uQ1JqTB-91nOqB4ekKmIi7uFZo" 
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

        await self.wait_for_loading(prompt, image_name)

        # Find downloaded image in download folder, change name, upload to cloud website while saving it's URL and removing from downloads
        image_url = cloudinary.uploader.upload_image(image_name, folder="Dalle Images/", use_filename = True).url
        os.remove(image_name)
        # Send embeded discord message with the generated IMG's URL 
        embed = discord.Embed(title=f"{interaction.user.name}'s Dalle Search Finished!", description=f"Prompt: {prompt}", color=discord.Color.from_rgb(0, 255, 0))
        embed.set_footer(text="Website Link: https://www.craiyon.com")
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)
        self.id_list.remove(interaction.user.id)
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
    def wait_for_loading(self, prompt, image_name):
        #Dalle Information
        LOADING_ELEMENT = "//*[contains(text(), 'This should not take long (up to 2 minutes)...')]"
        SCREENSHOT_BUTTON = "//*[contains(text(), 'Screenshot')]"
        RUN_BUTTON = '//*[@id="app"]/div/div/div[1]/button'
        POPUP_AGREE = '//*[@id="qc-cmp2-ui"]/div[2]/div/button[2]/span'
        SCREENSHOT_AREA = '//*[@id="app"]/div'
        VIDEO_POPUP_EXIT = '//*[@id="av-close-btn"]'

        #apply options to browser. Not currently used as headless causes program to crash
        #standard options work fine but window pops up when command runs
        options = webdriver.ChromeOptions()
        options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")

        #options.headless = True
        #user_agent = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16"
        #options.add_argument("--no-sandbox")
        #options.set_preference("general.useragent.override", user_agent)

        #initialise web driver
        driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=options)

        #navigate to dalle page
        driver.get("https://www.craiyon.com/")

        try:
            element = WebDriverWait(driver, 5).until(ec.presence_of_element_located((By.XPATH, POPUP_AGREE)))
            print("Popup found")
            driver.execute_script("arguments[0].click();", element)
            print("Popup accepted")
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

        screenshot = driver.find_element(By.XPATH, SCREENSHOT_AREA)
        screenshot.screenshot(image_name)

        # close driver
        driver.close()
        print("Driver closed. DALL-E img generation complete.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(dalle(bot), guilds=[discord.Object(id=config.TEEF2_SERVER)])