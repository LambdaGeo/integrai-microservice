@echo off
setlocal

set "OUTPUT=%~dp0radon_resultados.txt"
set "PYTHON_CMD=py"

pushd "%~dp0" >nul

%PYTHON_CMD% -m radon --version >nul 2>nul
if not errorlevel 1 goto run_radon
(
    echo Relatorio Radon - Complexidade Ciclomatica
    echo Projeto: %CD%
    echo Gerado em: %DATE% %TIME%
    echo.
    echo ERRO: o pacote radon nao foi encontrado no Python global.
    echo Instale com: py -m pip install radon
) > "%OUTPUT%"
popd >nul
echo Radon nao encontrado. Veja radon_resultados.txt.
exit /b 1

:run_radon
echo Gerando relatorio do Radon em radon_resultados.txt...

(
    echo Relatorio Radon - Complexidade Ciclomatica
    echo Projeto: %CD%
    echo Gerado em: %DATE% %TIME%
    echo Escopo: codigo de aplicacao relevante para o TCC.
    echo Excluidos: testes, migrations, dumps, scripts auxiliares, configuracoes e artefatos R.
    echo.
    echo ============================================================
    echo MICROSSERVICOS
    echo ============================================================
    echo.
    echo --- CC: Complexidade Ciclomatica ---
) > "%OUTPUT%"

set "EXIT_CODE=0"

%PYTHON_CMD% -m radon cc ^
    "avaliacoes-service\app" ^
    "gestantes-service\app" ^
    "users-service\app" ^
    "django_app\microservices" ^
    "django_app\apps\usuarios\backends.py" ^
    "django_app\apps\usuarios\decorator.py" ^
    "django_app\apps\usuarios\forms.py" ^
    "django_app\apps\usuarios\middleware.py" ^
    "django_app\apps\usuarios\models.py" ^
    "django_app\apps\usuarios\services.py" ^
    "django_app\apps\usuarios\urls.py" ^
    "django_app\apps\usuarios\views.py" ^
    "django_app\apps\gestantes\forms.py" ^
    "django_app\apps\gestantes\models.py" ^
    "django_app\apps\gestantes\services.py" ^
    "django_app\apps\gestantes\tasks.py" ^
    "django_app\apps\gestantes\templatetags\custom_filters.py" ^
    "django_app\apps\gestantes\urls.py" ^
    "django_app\apps\gestantes\views" ^
    "django_app\apps\core\context_processors.py" ^
    -a -s >> "%OUTPUT%" 2>&1

if errorlevel 1 set "EXIT_CODE=1"

(
    echo.
    echo --- MI: Indice de Manutenibilidade ---
) >> "%OUTPUT%"

%PYTHON_CMD% -m radon mi ^
    "avaliacoes-service\app" ^
    "gestantes-service\app" ^
    "users-service\app" ^
    "django_app\microservices" ^
    "django_app\apps\usuarios\backends.py" ^
    "django_app\apps\usuarios\decorator.py" ^
    "django_app\apps\usuarios\forms.py" ^
    "django_app\apps\usuarios\middleware.py" ^
    "django_app\apps\usuarios\models.py" ^
    "django_app\apps\usuarios\services.py" ^
    "django_app\apps\usuarios\urls.py" ^
    "django_app\apps\usuarios\views.py" ^
    "django_app\apps\gestantes\forms.py" ^
    "django_app\apps\gestantes\models.py" ^
    "django_app\apps\gestantes\services.py" ^
    "django_app\apps\gestantes\tasks.py" ^
    "django_app\apps\gestantes\templatetags\custom_filters.py" ^
    "django_app\apps\gestantes\urls.py" ^
    "django_app\apps\gestantes\views" ^
    "django_app\apps\core\context_processors.py" ^
    -s >> "%OUTPUT%" 2>&1

if errorlevel 1 set "EXIT_CODE=1"

(
    echo.
    echo --- RAW: Linhas de Codigo e Comentarios ---
) >> "%OUTPUT%"

%PYTHON_CMD% -m radon raw ^
    "avaliacoes-service\app" ^
    "gestantes-service\app" ^
    "users-service\app" ^
    "django_app\microservices" ^
    "django_app\apps\usuarios\backends.py" ^
    "django_app\apps\usuarios\decorator.py" ^
    "django_app\apps\usuarios\forms.py" ^
    "django_app\apps\usuarios\middleware.py" ^
    "django_app\apps\usuarios\models.py" ^
    "django_app\apps\usuarios\services.py" ^
    "django_app\apps\usuarios\urls.py" ^
    "django_app\apps\usuarios\views.py" ^
    "django_app\apps\gestantes\forms.py" ^
    "django_app\apps\gestantes\models.py" ^
    "django_app\apps\gestantes\services.py" ^
    "django_app\apps\gestantes\tasks.py" ^
    "django_app\apps\gestantes\templatetags\custom_filters.py" ^
    "django_app\apps\gestantes\urls.py" ^
    "django_app\apps\gestantes\views" ^
    "django_app\apps\core\context_processors.py" ^
    -s >> "%OUTPUT%" 2>&1

if errorlevel 1 set "EXIT_CODE=1"

(
    echo.
    echo ============================================================
    echo MONOLITICO
    echo ============================================================
    echo.
    echo --- CC: Complexidade Ciclomatica ---
) >> "%OUTPUT%"

if exist "..\integrai-app\django_app" (
    %PYTHON_CMD% -m radon cc ^
        "..\integrai-app\django_app\apps\usuarios\decorator.py" ^
        "..\integrai-app\django_app\apps\usuarios\forms.py" ^
        "..\integrai-app\django_app\apps\usuarios\models.py" ^
        "..\integrai-app\django_app\apps\usuarios\urls.py" ^
        "..\integrai-app\django_app\apps\usuarios\views.py" ^
        "..\integrai-app\django_app\apps\gestantes\forms.py" ^
        "..\integrai-app\django_app\apps\gestantes\models.py" ^
        "..\integrai-app\django_app\apps\gestantes\services.py" ^
        "..\integrai-app\django_app\apps\gestantes\tasks.py" ^
        "..\integrai-app\django_app\apps\gestantes\templatetags\custom_filters.py" ^
        "..\integrai-app\django_app\apps\gestantes\urls.py" ^
        "..\integrai-app\django_app\apps\gestantes\views" ^
        "..\integrai-app\django_app\apps\core\context_processors.py" ^
        -a -s >> "%OUTPUT%" 2>&1
    if errorlevel 1 set "EXIT_CODE=1"

    (
        echo.
        echo --- MI: Indice de Manutenibilidade ---
    ) >> "%OUTPUT%"

    %PYTHON_CMD% -m radon mi ^
        "..\integrai-app\django_app\apps\usuarios\decorator.py" ^
        "..\integrai-app\django_app\apps\usuarios\forms.py" ^
        "..\integrai-app\django_app\apps\usuarios\models.py" ^
        "..\integrai-app\django_app\apps\usuarios\urls.py" ^
        "..\integrai-app\django_app\apps\usuarios\views.py" ^
        "..\integrai-app\django_app\apps\gestantes\forms.py" ^
        "..\integrai-app\django_app\apps\gestantes\models.py" ^
        "..\integrai-app\django_app\apps\gestantes\services.py" ^
        "..\integrai-app\django_app\apps\gestantes\tasks.py" ^
        "..\integrai-app\django_app\apps\gestantes\templatetags\custom_filters.py" ^
        "..\integrai-app\django_app\apps\gestantes\urls.py" ^
        "..\integrai-app\django_app\apps\gestantes\views" ^
        "..\integrai-app\django_app\apps\core\context_processors.py" ^
        -s >> "%OUTPUT%" 2>&1
    if errorlevel 1 set "EXIT_CODE=1"

    (
        echo.
        echo --- RAW: Linhas de Codigo e Comentarios ---
    ) >> "%OUTPUT%"

    %PYTHON_CMD% -m radon raw ^
        "..\integrai-app\django_app\apps\usuarios\decorator.py" ^
        "..\integrai-app\django_app\apps\usuarios\forms.py" ^
        "..\integrai-app\django_app\apps\usuarios\models.py" ^
        "..\integrai-app\django_app\apps\usuarios\urls.py" ^
        "..\integrai-app\django_app\apps\usuarios\views.py" ^
        "..\integrai-app\django_app\apps\gestantes\forms.py" ^
        "..\integrai-app\django_app\apps\gestantes\models.py" ^
        "..\integrai-app\django_app\apps\gestantes\services.py" ^
        "..\integrai-app\django_app\apps\gestantes\tasks.py" ^
        "..\integrai-app\django_app\apps\gestantes\templatetags\custom_filters.py" ^
        "..\integrai-app\django_app\apps\gestantes\urls.py" ^
        "..\integrai-app\django_app\apps\gestantes\views" ^
        "..\integrai-app\django_app\apps\core\context_processors.py" ^
        -s >> "%OUTPUT%" 2>&1
    if errorlevel 1 set "EXIT_CODE=1"
) else (
    echo Pasta do monolitico nao encontrada: ..\integrai-app\django_app >> "%OUTPUT%"
    set "EXIT_CODE=1"
)

popd >nul

if not "%EXIT_CODE%"=="0" (
    echo Radon terminou com erro. Veja radon_resultados.txt.
    exit /b %EXIT_CODE%
)

echo Relatorio gerado em radon_resultados.txt.

