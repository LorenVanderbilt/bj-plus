-- ./run.sh's one -autoboot_script (MAME runs only one): runs each script named in RUN_SCRIPTS, separated by ";" -
-- the shared M save key, tools/difficulty.lua with --difficulty, and any -autoboot_script given after --.
for path in string.gmatch(os.getenv("RUN_SCRIPTS") or "", "[^;]+") do
    dofile(path)
end
