import os
import unittest
import yaml

class TestDevOpsDeployment(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.deploy_dir = os.path.join(self.base_dir, "deploy")
        self.systemd_dir = os.path.join(self.deploy_dir, "systemd")

    def test_requirements_txt_contains_all_dependencies(self):
        req_path = os.path.join(self.base_dir, "requirements.txt")
        self.assertTrue(os.path.exists(req_path), "requirements.txt must exist")
        
        with open(req_path, "r", encoding="utf-8") as f:
            content = f.read()

        expected_dependencies = [
            "Flask>=3.0.0",
            "Flask-WTF>=1.2.0",
            "python-telegram-bot[job-queue]>=20.7",
            "jdatetime>=5.0.0",
            "Pillow>=10.0.0",
            "requests>=2.31.0",
            "python-dotenv>=1.0.0",
            "tzdata>=2024.1",
            "gunicorn>=21.2.0",
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-mock>=3.12.0",
        ]

        for dep in expected_dependencies:
            self.assertIn(dep, content, f"Dependency '{dep}' missing in requirements.txt")

    def test_systemd_units_and_timer_exist_and_configured(self):
        # 1. psychobot-web.service
        web_service = os.path.join(self.systemd_dir, "psychobot-web.service")
        self.assertTrue(os.path.exists(web_service), "psychobot-web.service must exist")
        with open(web_service, "r", encoding="utf-8") as f:
            web_content = f.read()
        self.assertIn("Restart=on-failure", web_content)
        self.assertIn("RestartSec=5s", web_content)
        self.assertIn("EnvironmentFile=/opt/psychology_bot/.env", web_content)
        self.assertIn("WorkingDirectory=/opt/psychology_bot", web_content)
        self.assertIn("127.0.0.1:5000", web_content)
        self.assertIn("app:app", web_content)

        # 2. psychobot-bot.service
        bot_service = os.path.join(self.systemd_dir, "psychobot-bot.service")
        self.assertTrue(os.path.exists(bot_service), "psychobot-bot.service must exist")
        with open(bot_service, "r", encoding="utf-8") as f:
            bot_content = f.read()
        self.assertIn("Restart=on-failure", bot_content)
        self.assertIn("RestartSec=5s", bot_content)
        self.assertIn("EnvironmentFile=/opt/psychology_bot/.env", bot_content)
        self.assertIn("WorkingDirectory=/opt/psychology_bot", bot_content)
        self.assertIn("main.py", bot_content)

        # 3. psychobot-report.service
        report_service = os.path.join(self.systemd_dir, "psychobot-report.service")
        self.assertTrue(os.path.exists(report_service), "psychobot-report.service must exist")
        with open(report_service, "r", encoding="utf-8") as f:
            report_content = f.read()
        self.assertIn("daily_report.py", report_content)
        self.assertIn("Type=oneshot", report_content)

        # 4. psychobot-report.timer
        report_timer = os.path.join(self.systemd_dir, "psychobot-report.timer")
        self.assertTrue(os.path.exists(report_timer), "psychobot-report.timer must exist")
        with open(report_timer, "r", encoding="utf-8") as f:
            timer_content = f.read()
        self.assertIn("OnCalendar=*-*-* 21:00:00", timer_content)
        self.assertIn("Persistent=true", timer_content)
        self.assertIn("Unit=psychobot-report.service", timer_content)

        # 5. deploy/README.md
        deploy_readme = os.path.join(self.deploy_dir, "README.md")
        self.assertTrue(os.path.exists(deploy_readme), "deploy/README.md must exist")

    def test_dockerfile_and_compose_configurations(self):
        # 1. Dockerfile
        dockerfile_path = os.path.join(self.base_dir, "Dockerfile")
        self.assertTrue(os.path.exists(dockerfile_path), "Dockerfile must exist")
        with open(dockerfile_path, "r", encoding="utf-8") as f:
            dockerfile_content = f.read()
        self.assertIn("python:3.12-slim", dockerfile_content)
        self.assertIn("appuser", dockerfile_content)
        self.assertIn("1000", dockerfile_content)
        self.assertIn("libjpeg", dockerfile_content)
        self.assertIn("zlib", dockerfile_content)
        self.assertIn("/app/private_uploads", dockerfile_content)

        # 2. docker-compose.yml
        compose_path = os.path.join(self.base_dir, "docker-compose.yml")
        self.assertTrue(os.path.exists(compose_path), "docker-compose.yml must exist")
        with open(compose_path, "r", encoding="utf-8") as f:
            compose_data = yaml.safe_load(f)

        self.assertIn("services", compose_data)
        self.assertIn("web", compose_data["services"])
        self.assertIn("bot", compose_data["services"])
        self.assertIn("volumes", compose_data)
        self.assertIn("db_data", compose_data["volumes"])
        self.assertIn("upload_data", compose_data["volumes"])

        web_env = compose_data["services"]["web"].get("env_file", [])
        self.assertIn(".env", web_env)

    def test_github_actions_ci_workflow(self):
        ci_path = os.path.join(self.base_dir, ".github", "workflows", "ci.yml")
        self.assertTrue(os.path.exists(ci_path), ".github/workflows/ci.yml must exist")
        with open(ci_path, "r", encoding="utf-8") as f:
            ci_content = f.read()

        self.assertIn("push:", ci_content)
        self.assertIn("pull_request:", ci_content)
        self.assertIn("main", ci_content)
        self.assertIn("3.12", ci_content)
        self.assertIn("requirements.txt", ci_content)
        self.assertIn("pytest tests/ -v", ci_content)

if __name__ == "__main__":
    unittest.main()
