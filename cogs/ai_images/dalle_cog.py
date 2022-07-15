import discord
from discord import Interaction, app_commands
from discord.ext import commands, tasks
from selenium import webdriver
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

        await self.wait_for_loading(prompt)

        # Generate unique image name based on author of command
        image_name = f"Dalle_Image_{interaction.user.id}_{str(uuid.uuid4().hex)}"

        # Find downloaded image in download folder, change name, upload to cloud website while saving it's URL and removing from downloads
        path = 'C:/Users/james/Downloads/'
        for i in os.listdir(path):
            if i.startswith("craiyon_"):
                os.rename(path + i, path + f"{image_name}")
                image_url = cloudinary.uploader.upload_image(f"{path}{image_name}",
                    folder="Dalle Images/",
                    use_filename = True).url
                os.remove(path + f"{image_name}")
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
    def wait_for_loading(self, prompt):
        dir_path = os.getcwd()
        cogs_dir = os.path.dirname(dir_path)
        master_dir = os.path.dirname(cogs_dir)
        #Dalle Information
        LOADING_ELEMENT = "//*[contains(text(), 'This should not take long (up to 3 minutes)...')]"
        SCREENSHOT_BUTTON = "//*[contains(text(), 'Screenshot')]"
        RUN_BUTTON = '//*[@id="app"]/div/div/div[1]/button'
        POPUP_REJECT_ALL = "//*[contains(text(), 'Reject All')]"

        #apply options to browser. Not currently used as headless causes program to crash
        #standard options work fine but window pops up when command runs
        options = webdriver.FirefoxOptions()
        options.headless = True

        #initialise web driver
        driver = webdriver.Firefox(executable_path=master_dir + 'Command_Executables\geckodriver\geckodriver.exe', options=options)

        #navigate to dalle page
        driver.get("https://www.craiyon.com/")

        try:
            element = WebDriverWait(driver, 2).until(ec.presence_of_element_located((By.XPATH, POPUP_REJECT_ALL)))
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

            # Wait for screenshot button to become clickable and click. Then wait for download
            WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.XPATH, SCREENSHOT_BUTTON)))
            element = driver.find_element(By.XPATH, SCREENSHOT_BUTTON)
            driver.execute_script("arguments[0].click();", element)
            print("Screenshot taken.")
            time.sleep(3)
        except TimeoutException:
            return print("Could not find loading element in time.")
        except ElementClickInterceptedException:
            return print("Element Click Intercepted Exception Raised.")
        except UnexpectedAlertPresentException:
            return print("Unexpected Alart Present")

        # close driver
        driver.close()
        print("Driver closed. DALL-E img generation complete.")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(dalle(bot), guilds=[discord.Object(id=config.TEEF2_SERVER)])