import argparse
import hashlib
import subprocess


def clone_homebrew_tap_repo():
    subprocess.run(['git', 'clone', 'https://github.com/QtonSolutions/homebrew-tap.git'])


def generate_sha256_digest():
    global sha256_digest
    sha256 = hashlib.sha256()
    with open(args.archive, 'rb') as archive:
        file_buffer_size = 64 * 1024
        while True:
            data = archive.read(file_buffer_size)
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def write_updated_brew_formula(version, sha256_digest):
    with open('homebrew-tap/Formula/sessh.rb', 'w') as formula_file:
        formula = f'''class Sessh < Formula
    homepage "https://github.com/QtonSolutions/sessh"
    url "https://github.com/QtonSolutions/sessh/releases/download/{version}/sessh-{version}-osx.gz"
    sha256 "{sha256_digest}"

    bottle :unneeded

    def install
        bin.install "sessh"
    end

    test do
        assert_match version.to_s, shell_output("#{bin}/sessh --version")
    end
end'''
        formula_file.write(formula)


def commit_and_push(version):
    repository_path = './homebrew-tap'
    subprocess.run(['git', 'add', 'Formula/sessh.rb'], cwd=repository_path)
    subprocess.run(['git', 'commit', '-m', f'Publish {version}'], cwd=repository_path)
    subprocess.run(['git', 'push'], cwd=repository_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Publish new release to QtonSolutions Homebrew tap")
    parser.add_argument('version', help="version tag")
    parser.add_argument('archive', help="path to gzipped archive with sessh binary")

    args = parser.parse_args()

    clone_homebrew_tap_repo()
    sha256_digest = generate_sha256_digest()
    write_updated_brew_formula(args.version, sha256_digest)
    commit_and_push(args.version)
