import datetime
import logging
import os
import time
import sys
import traceback

from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


DEBUG = True
ATTACH_MODE = False
LONG_INTERVAL = 5
SHORT_INTERVAL = 3

config = {
    'url': 'https://smartcourse.hust.edu.cn/mooc-smartcourse/mooc2-ans/mooc2-ans/mycourse/stu?courseid=17310000019056&clazzid=17310000010770&cpi=17310000137156&enc=3a6de4f059b5aae1803055b41eeb4aa3&t=1741790144317&pageHeader=1&v=0',
    'userData': 'C:\\Users\\15358\\AppData\\Local\\Google\\Chrome\\User Data',
    'startChapter': 3,
    'startTask': 1,
    'endChapter': 7,
    'endTask': 15,
}

chapter_info = {
    2: 10,
    3: 10,
    4: 13,
    5: 12,
    6: 18,
    7: 15,
    8: 12,
    9: 18,
    10: 13,
    11: 10,
}

class AutoCourse:



    def __init__(self):

        self.__init_logger()
        chrome_options = Options()
        if ATTACH_MODE:
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        else:
            chrome_options.add_argument(
                f"--user-data-dir={config['userData']}")
            if not DEBUG:
                chrome_options.add_argument("--headless")  # 启用无头模式
                chrome_options.add_argument("--disable-gpu")  # 禁用 GPU 加速
        self.__driver = webdriver.Chrome(options=chrome_options)
        self.__current_chapter = config['startChapter']
        self.__current_task_id = config['startTask']
        self.__current_task = ""


    def __init_logger(self):
        self.logger = logging.getLogger('AutoRun')
        filename = time.strftime("./logs/%y_%m_%d_%a.log")
        if not os.path.exists('./logs'):
            os.mkdir('logs')

        # 设置handler的格式
        formatter = logging.Formatter(
            "%(asctime)s| %(levelname)-8s | %(module)s:%(funcName)s:%(lineno)d - %(message)s")

        stdout_handler = logging.StreamHandler(sys.stdout)
        file_handler = logging.FileHandler(filename)  # 指定日志文件名

        stdout_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # 添加handler到logger中
        self.logger.addHandler(stdout_handler)
        self.logger.addHandler(file_handler)

        self.logger.setLevel(logging.DEBUG)

        self.logger.info('=' * 100)
        self.logger.info(f"= Test begin: {time.strftime('%Y/%m/%d %H:%M:%S')}")
        self.logger.info('=' * 100)

    def __switch_window(self):
        for handle in self.__driver.window_handles:
            self.__driver.switch_to.window(handle)
            # self.logger.debug(f"{self.__driver.current_url}")
            if "https://smartcourse.hust.edu.cn/" in self.__driver.current_url:
                break

    def __prepare(self):
        if ATTACH_MODE:
            # 新建标签页并访问目标网站（自动继承登录状态）
            script = f'window.open("{config["url"]}");'
            self.__driver.execute_script(script)
        else:
            self.__driver.get(config["url"])

        # 切换到新标签页
        self.__switch_window()

        iframe = self.__driver.find_element(By.XPATH, "//iframe[@id='frame_content-zj']")
        self.__driver.switch_to.frame(iframe)
        self.logger.info('Switch to iframe: frame_content-zj')
        time.sleep(LONG_INTERVAL)

        # TODO get chapter info

        start_chapter = self.__driver.find_element(by=By.XPATH, value=f"//*[@class='chapter_unit'][{config['startChapter']}]")
        self.logger.info(f"Start from Chapter {config['startChapter']}")
        # #fanyaChapter > div > div.chapter_body.xs_table > div.chapter_td > div:nth-child(3)
        start_item = start_chapter.find_element(by=By.CSS_SELECTOR, value='.catalog_level > ul > li')
        self.__driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", start_item)
        time.sleep(SHORT_INTERVAL)
        start_item.click()
        self.logger.info(f'Click first item in Chapter {config["startChapter"]}')
        time.sleep(LONG_INTERVAL)

    def __current_task_finished(self) -> bool:
        self.__switch_window()

        iframe = self.__driver.find_element(By.XPATH, "//iframe[@id='iframe']")
        self.__driver.switch_to.frame(iframe)

        status = self.__driver.find_element(by=By.CSS_SELECTOR, value='.ans-job-icon.ans-job-icon-clear')
        self.logger.debug(f"Status: {status.get_attribute('aria-label')}")

        if status.get_attribute('aria-label') == "任务点已完成":
            return True
        else:
            return False

    def __play_video(self) -> bool:
        try:
            iframe = self.__driver.find_element(by=By.CSS_SELECTOR, value=".ans-attach-online.ans-insertvideo-online")
            self.__driver.switch_to.frame(iframe)
            self.__driver.find_element(by=By.CSS_SELECTOR, value=".vjs-big-play-button").click()
            self.logger.info(f"Play video of {self.__current_task}")
            return True
        except NoSuchElementException:
            self.logger.warning(f"No video play button found in [{self.__current_chapter}.{self.__current_task_id}]")
            return False

    def __find_next_task(self):
        self.__switch_window()

        right_panel = self.__driver.find_element(by=By.CSS_SELECTOR, value=".chapter")
        chapter = self.__driver.find_element(by=By.CSS_SELECTOR, value=f".chapter > .onetoone.posCatalog > ul > li:nth-child({self.__current_chapter})")
        next_task = chapter.find_element(by=By.CSS_SELECTOR, value=f".posCatalog_level > ul > li:nth-child({self.__current_task_id})")

        self.logger.info(f"Found next task {self.__current_chapter}.{self.__current_task_id}, scroll into view")
        self.__driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_task)
        # 获取目标元素相对于容器的垂直位置
        # script = """
        #     var container = arguments[0];
        #     var element = arguments[1];
        #     return element.offsetTop - container.offsetTop;
        # """
        # offset_top = self.__driver.execute_script(script, right_panel, next_task)
        # self.logger.info(f"offset_top: {offset_top}")
        #
        # # 滚动到目标位置（使用平滑滚动）
        # self.__driver.execute_script(
        #     "arguments[0].scrollTo({top: arguments[1], behavior: 'smooth'});",
        #     right_panel,
        #     offset_top
        # )
        time.sleep(SHORT_INTERVAL)

        chapter = self.__driver.find_element(by=By.CSS_SELECTOR,
                                             value=f".chapter > .onetoone.posCatalog > ul > li:nth-child({self.__current_chapter})")
        next_task = chapter.find_element(by=By.CSS_SELECTOR,
                                         value=f".posCatalog_level > ul > li:nth-child({self.__current_task_id})")
        next_task.click()
        time.sleep(LONG_INTERVAL)

    def __wait_for_finished(self):
        start_time = time.time()
        end_time = start_time + 600
        timeout = False
        while not self.__current_task_finished() and not timeout:
            # check every 10 seconds
            self.count_down(seconds=10)
            timeout = time.time() > end_time

        if timeout:
            self.logger.warning("Time out")
        else:
            self.logger.info(f"[{self.__current_chapter}.{self.__current_task_id}] [{self.__current_task}] is finished")

    def count_down(self, weeks=0, days=0, hours=0, minutes=0, seconds=0):
        remain_time = datetime.timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
        while remain_time.total_seconds() > 0:
            time.sleep(1)
            remain_time -= datetime.timedelta(seconds=1)
            print("\r 距离下次检查：{}".format(remain_time), end="", flush=True)
        print("")

    def quit(self):
        self.__driver.quit()

    def work(self):
        try:
            self.__prepare()

            while self.__current_chapter <= config['endChapter'] and self.__current_task_id <= config['endTask']:
                self.logger.info("-" * 50)
                self.__find_next_task()
                self.__current_task = self.__driver.find_element(by=By.XPATH, value="//*[@class='prev_title']").get_attribute('title')
                self.logger.info(f"Current task: {self.__current_task}")

                if not self.__current_task_finished():
                    success = self.__play_video()
                    if success:
                        self.__wait_for_finished()
                else:
                    self.logger.info(f"[{self.__current_chapter}.{self.__current_task_id}] [{self.__current_task}] is already finished, skip to next task")

                self.__current_task_id += 1
                if self.__current_task_id > chapter_info[self.__current_chapter]:
                    self.__current_chapter += 1
                    self.__current_task_id = 1
            self.logger.info("-" * 50)
            self.logger.info("All tasks done!")
        except KeyboardInterrupt:
            self.logger.info("Automation interrupted")
        except Exception as e:
            self.logger.error(e)
            self.logger.info(traceback.format_exc())
        finally:
            # input("Press Enter to continue...")
            self.quit()


if __name__ == '__main__':
    auto = AutoCourse()
    auto.work()

    # Windows
    # "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
