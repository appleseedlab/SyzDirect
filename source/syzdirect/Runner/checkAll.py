#Some potential goals for script improvement in future:
#- Input verification for xidxCheck
#- Check if kcov.h header added
#- Check if duplicates exist for multiple xidx values
#- Use pandas to get range values from dataset.xlsx automatically & avoid asking user for range

import os
import re
import multiprocessing

def read_file_with_encodings(file_path, encodings=('utf-8', 'latin-1')):
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(f"Unable to decode {file_path} with provided encodings")

def check_instrumentation(kernel_dir): #Process kernel to check for kcov_mark_block
    xidx_pattern = re.compile(r'kcov_mark_block\((\d+)\)')
    xidx_values = set()
    instrumented_files = []

    #Traverse kernel directories to check for kcov_mark_block
    for root, dirs, files in os.walk(kernel_dir):
        for file in files:
            if file.endswith('.c') or file.endswith('.h'):
                file_path = os.path.join(root, file)
                try:
                    content = read_file_with_encodings(file_path)
                    matches = xidx_pattern.findall(content)
                    if matches:
                        instrumented_files.append(file_path)
                        xidx_values.update(matches)
                except UnicodeDecodeError as e:
                    print(f"Error reading {file_path}: {e}")

    return xidx_values, instrumented_files

def check_kcov(kernel_dir):
    kcovcrej_files = []
    kcovhrej_files = []
    kernel_kernel_dir = os.path.join(kernel_dir, 'kernel')  #kernel directory within kernel where kcov.c is
    kernel_linux_dir = os.path.join(kernel_dir, 'include/linux')  #linux directory where kcov.h is
    
    #Check kernel directory to look for kcov.c rejects
    for root, dirs, files in os.walk(kernel_kernel_dir):
        for file in files:
            if file.endswith('.rej'):
                file_path = os.path.join(root, file)
                kcovcrej_files.append(file_path)

    #Check linux directory to look for kcov.h rejects
    for root, dirs, files in os.walk(kernel_linux_dir):
        for file in files:
            if file.endswith('.rej'):
                file_path = os.path.join(root, file)
                kcovhrej_files.append(file_path)

    return kcovcrej_files, kcovhrej_files

def process_kernel(idx, kernel_base_dir, xidx_check): #Process kernel to check for xidx values
    kernel_dir = os.path.join(kernel_base_dir, f'case_{idx}')
    if not os.path.exists(kernel_dir):
        return f"Kernel directory for idx {idx} doesn't exist"

    #Kernel instrumentation checks
    xidx_values, instrumented_files = check_instrumentation(kernel_dir)
    if len(xidx_values) == 0:
        result = f"Kernel {idx} has no instrumentation"
    elif xidx_check == True: #If user wants to check if each kernel only has one kcov_mark_block 
        if len(xidx_values) == 1:
            result = f"Kernel {idx} correctly instrumented with xidx: {list(xidx_values)[0]}, found in {list(instrumented_files)[0]}" 
        else:
            result = (f"Kernel {idx} has incorrect instrumentation:\n"
                  f"  xidx values found: {xidx_values}\n"
                  f"  Instrumented files: {instrumented_files}")
    elif xidx_check == False: #If user has multiple kcov_mark_blocks in their kernels
        result = (f"Kernel is instrumented at:\n"
                  f"  xidx values found: {xidx_values}\n"
                  f"  Instrumented files: {instrumented_files}")

    #KCOV rejection files
    kcovcrej_files, kcovhrej_files = check_kcov(kernel_dir)
    if kcovcrej_files:
         result += f"\nKernel {idx} has a kcov.c rejection found at {kcovcrej_files[0]}"
    if kcovhrej_files:
         result += f"\nKernel {idx} has a kcov.h rejection found at {kcovhrej_files[0]}"

    return result

def main() -> None:

    #Get user input for path
    kernel_base_dir: str = input("Please provide the path to SyzDirect's kernel sources directory. Example: /home/yourName/SyzDirect/source/syzdirect/Runner/workdir/srcs: ").strip()

    if not os.path.exists(kernel_base_dir):
        print(f"Sources directory {kernel_base_dir} doesn't exist. Exiting")
        return

    #Get user input for range
    while True:
        try:
            idxInt1: int = int(input("What is the first number in the range of values that you need checked? Usually, this is set to 0. Input: ").strip())
            break
        except ValueError:
            print("Please enter a valid integer.")

    while True:
        try:
            idxInt2: int = int(input("What is the last number in the range of values that you need checked? Input: ").strip())
            break
        except ValueError:
            print("Please enter a valid integer.")

    if idxInt1 > idxInt2:
        print("The first number should be less than or equal to the last number. Exiting.")
        return

    idx_list: range = range(idxInt1, idxInt2 + 1)

    #Ask user if they would like to check for duplicate xidx values
    xidxCheck: bool

    if input("Do the kernels you've instrumented only have one xidx value of 0 per kernel? Input y/n:").strip().lower() == "y": 
        xidxCheck = True
    else:
        xidxCheck = False

    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        results: list[str] = pool.starmap(process_kernel, [(idx, kernel_base_dir, xidxCheck) for idx in idx_list]) #Iterate process_kernel through all kernels 

    for result in results:
        print(result)

if __name__ == "__main__":
    main()
