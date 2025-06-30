"""
Swagger API Agent 安装配置
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README 文件
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取 requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = requirements_file.read_text(encoding="utf-8").strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="swagger-api-agent",
    version="1.0.0",
    author="Swagger API Agent Team",
    author_email="team@swagger-api-agent.com",
    description="自动化自然语言调用 API 接口的智能代理",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swagger-api-agent/swagger-api-agent",
    project_urls={
        "Bug Tracker": "https://github.com/swagger-api-agent/swagger-api-agent/issues",
        "Documentation": "https://github.com/swagger-api-agent/swagger-api-agent/blob/main/docs/",
        "Source Code": "https://github.com/swagger-api-agent/swagger-api-agent",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=22.0",
            "flake8>=5.0",
            "mypy>=1.0",
        ],
        "test": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "requests-mock>=1.10",
        ],
    },
    entry_points={
        "console_scripts": [
            "swagger-api-agent=swagger_api_agent.cli:main",
            "swagger-web-api=swagger_api_agent.web_api:main",
        ],
    },
    include_package_data=True,
    package_data={
        "swagger_api_agent": ["*.yaml", "*.yml", "*.json"],
    },
    zip_safe=False,
    keywords=[
        "swagger", 
        "openapi", 
        "api", 
        "agent", 
        "llm", 
        "natural-language", 
        "automation",
        "deepseek",
        "flask",
        "cli"
    ],
)
