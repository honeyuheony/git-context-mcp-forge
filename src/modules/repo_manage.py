from git import Repo
import shutil
import os
import subprocess
import platform
import logging


def clone_repo_url(repo_url, local_path):
    """
    [추가 설치가 필요한 라이브러리]
    - gitpython

    [변수]
    - repo_url: clone 받을 repository url 입력
    - local_path: clone 받을 디렉토리
    """

    try:
        repo = Repo.clone_from(repo_url, local_path)
        logging.info(f"리포지토리 클론 완료: {repo.working_dir}")
        # print(f"리포지토리 클론 완료: {repo_url}")
        return repo
    except Exception as e:
        # print(f"에러 발생: {str(e)}")
        # logging.error(e)
        raise RuntimeError(f"clone_repo_url :: 에러 발생: {str(e)}")

def remove_repository(local_path):
    """
    [변수]
    - local_path: 삭제할 directory
    [subprocess로 .git을 삭제하는 이유]
    - shutil로 삭제하려고 하면, .git 폴더는 삭제가 안됨
    """

    try:
        # .git 삭제
        git_path = os.path.join(local_path, '.git')
        git_path = os.path.normpath(git_path)  # 경로 정규화
        
        if os.path.exists(git_path):
            # 운영체제에 따라 적절한 명령어 사용
            if platform.system() == 'Windows':
                subprocess.run(f'rd /s /q "{git_path}"', shell=True, check=True)
            else:  # macOS, Linux
                subprocess.run(f'rm -rf "{git_path}"', shell=True, check=True)
            # print(f"'.git' 디렉토리 삭제 완료")
        else:
            # print()
            logging.error(f"'.git' 디렉토리를 찾을 수 없습니다")

        # 디렉토리 삭제
        shutil.rmtree(local_path)
        # print(f"'{local_path}' 삭제 완료")
    except Exception as e:
        # print(f"에러 발생: {str(e)}")
        logging.error(f"에러 발생: {str(e)}")

# def main():
#     repo_url = "https://github.com/LangChain-OpenTutorial/LangChain-OpenTutorial"
#     local_path = "./repo_data"
#
#     clone_repo_url(repo_url, local_path)
#
# if __name__ == "__main__":
#     main()