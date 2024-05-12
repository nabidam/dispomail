from setuptools import setup

setup(
    name="dispomail",
    version="0.1.0",
    description="Package that helps you to create and manage temp and disposable mail accounts (mail.tm for now)",
    url="https://github.com/nabidam/dispomail",
    author="Navid",
    author_email="navidabbaspoor@gmail.com",
    license="MIT License",
    packages=["dispomail"],
    install_requires=[
        "requests",
    ],
)
