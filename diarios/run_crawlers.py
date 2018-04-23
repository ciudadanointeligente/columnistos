from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from scrapy import Spider
import importlib
import sys, inspect
import pkgutil
import importlib
import os
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer

configure_logging()

class ColumnistosClassesGetterMixin(object):
    def __init__(self, settings, country):
        self.settings = settings
        module_name_where_classes_are = self.settings.get('NEWSPIDER_MODULE')
        self.module_name = module_name_where_classes_are + '.{country}'
        self.country = country

    def get_classes(self):
        module_name = self.module_name.format(country=self.country)
        module = importlib.import_module(module_name)
        pkgpath = os.path.dirname(module.__file__)
        file_names = [name for _, name, _ in pkgutil.iter_modules([pkgpath])]
        classes = []
        for f in file_names:
            crawler_container_file = module_name + "." + f
            crawler_container_module = importlib.import_module(crawler_container_file)
            for name, cls_ in inspect.getmembers(crawler_container_module):
                if inspect.isclass(cls_) and issubclass(cls_, Spider):
                    classes.append(cls_)
        return classes

class ColumnistosCrawlerRunner(ColumnistosClassesGetterMixin):
    def __init__(self, settings, country):
        super().__init__(settings, country)

    def run_crawlers(self):
        classes = self.get_classes()
        self._crawl(classes)
        reactor.run()

    @defer.inlineCallbacks
    def _crawl(self, classes):
        _runner = CrawlerRunner(self.settings)
        for cls_ in classes:
            yield _runner.crawl(cls_)
        reactor.stop()


if __name__ == "__main__":
    _settings = get_project_settings()
    _country = _settings.get('COUNTRY', 'ar')
    runner = ColumnistosCrawlerRunner(_settings, _country)
    runner.run_crawlers()
