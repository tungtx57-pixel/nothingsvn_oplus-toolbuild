#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to patch smali files:
- Find method: getRestartServiceInRecentList
- Find line: iget-boolean vx, py, Lcom/android/server/am/OplusAppStartupConfig;->isExpVersion:Z
- Add line below: const/4 vx, 0x1
"""

import os
import re
import sys
import argparse
from pathlib import Path


def find_smali_files(directory):
    """Find all .smali files in directory recursively."""
    smali_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.smali'):
                smali_files.append(os.path.join(root, file))
    return smali_files


def patch_file(file_path, dry_run=False):
    """
    Patch a single smali file.
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    in_target_method = False
    method_indent = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check if we're entering the target method
        if '.method' in line and 'getRestartServiceInRecentList' in line:
            in_target_method = True
            # Extract indentation (usually 0 for method declaration)
            method_indent = line[:len(line) - len(line.lstrip())]
            print(f"  Found method: getRestartServiceInRecentList")
        
        # Check if we're exiting the method
        elif in_target_method and '.end method' in line:
            in_target_method = False
            print(f"  End of method")
        
        # Check for the target iget-boolean instruction
        elif in_target_method:
            # Pattern: iget-boolean vX, pY, Lcom/android/server/am/OplusAppStartupConfig;->isExpVersion:Z
            pattern = r'^\s*iget-boolean\s+v(\d+),\s*p\d+,\s*Lcom/android/server/am/OplusAppStartupConfig;->isExpVersion:Z'
            match = re.search(pattern, line)
            
            if match:
                register_num = match.group(1)
                # Get the indentation of the current line
                indent = line[:len(line) - len(line.lstrip())]
                
                # Create the const/4 instruction
                const_instruction = f"{indent}const/4 v{register_num}, 0x1\n"
                
                print(f"  Found iget-boolean with register v{register_num}")
                print(f"  Adding: const/4 v{register_num}, 0x1")
                
                # Check if the next line is already our patch
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if f"const/4 v{register_num}, 0x1" in next_line:
                        print(f"  Patch already applied, skipping...")
                        i += 1
                        continue
                
                # Add the const/4 instruction
                new_lines.append(const_instruction)
                new_lines.append("\n")  # Add blank line for readability
                modified = True
        
        i += 1
    
    # Write the modified content back
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] File patched successfully")
    elif modified and dry_run:
        print(f"  [DRY RUN] Would patch this file")
    
    return modified


def patch_google_restrict_info(file_path, dry_run=False):
    """
    Patch isGoogleRestricInfoOn method to always return false.
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    in_target_method = False
    method_start_line = -1
    method_indent = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if we're entering the target method
        if '.method private isGoogleRestricInfoOn(I)Ljava/lang/Boolean;' in line:
            in_target_method = True
            method_start_line = i
            method_indent = line[:len(line) - len(line.lstrip())]
            print(f"  Found method: isGoogleRestricInfoOn")
            
            # Add the method signature
            new_lines.append(line)
            
            # Skip all content until .end method
            i += 1
            while i < len(lines) and '.end method' not in lines[i]:
                i += 1
            
            # Check if already patched
            if i > method_start_line + 1:
                # Check if the method body is already our patch
                expected_body_line1 = f"{method_indent}    const/4 v0, 0x0\n"
                expected_body_line2 = f"{method_indent}    return v0\n"
                
                if (method_start_line + 1 < len(lines) and 
                    method_start_line + 2 < len(lines) and
                    lines[method_start_line + 1].strip() == "const/4 v0, 0x0" and
                    lines[method_start_line + 2].strip() == "return v0"):
                    print(f"  Patch already applied, skipping...")
                    # Add all the skipped lines back
                    for j in range(method_start_line + 1, i + 1):
                        new_lines.append(lines[j])
                    i += 1
                    in_target_method = False
                    continue
            
            # Add the new method body
            new_lines.append(f"{method_indent}    .registers 2\n")
            new_lines.append("\n")
            new_lines.append(f"{method_indent}    const/4 v0, 0x0\n")
            new_lines.append("\n")
            new_lines.append(f"{method_indent}    return v0\n")
            
            # Add .end method
            if i < len(lines):
                new_lines.append(lines[i])
            
            print(f"  Replaced method body with: const/4 v0, 0x0 + return v0")
            modified = True
            in_target_method = False
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # Write the modified content back
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] File patched successfully")
    elif modified and dry_run:
        print(f"  [DRY RUN] Would patch this file")
    
    return modified


def patch_update_gms_restrict(file_path, dry_run=False):
    """
    Patch updateGmsRestrict method to return immediately after .registers.
    
    Adds: return-void after .registers line
    This effectively disables the entire method.
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    in_target_method = False
    method_indent = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check if we're entering updateGmsRestrict method
        if '.method public updateGmsRestrict()V' in line:
            in_target_method = True
            method_indent = line[:len(line) - len(line.lstrip())]
            print(f"  Found method: updateGmsRestrict")
            i += 1
            continue
        
        # Check if we're leaving the method
        if in_target_method and '.end method' in line:
            in_target_method = False
            i += 1
            continue
        
        # Look for .registers line in target method
        if in_target_method and '.registers' in line:
            # Check if next line is already return-void (patch already applied)
            if i + 1 < len(lines) and 'return-void' in lines[i + 1]:
                print(f"  Patch already applied, skipping...")
            else:
                # Add return-void after .registers
                new_lines.append(f"{method_indent}    return-void\n")
                print(f"  Added return-void after .registers")
                modified = True
            in_target_method = False  # We're done with this method
        
        i += 1
    
    # Write the modified content back
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] File patched successfully")
    elif modified and dry_run:
        print(f"  [DRY RUN] Would patch this file")
    
    return modified


def patch_hans_feature_enable(file_path, dry_run=False):
    """
    Patch isHansFeatureEnable method to override isChinaMode and isExpRegion results.
    
    - After isChinaMode()->move-result: add const/4 vX, 0x0
    - After isExpRegion()->move-result: add const/4 vX, 0x1
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    in_target_method = False
    method_indent = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        new_lines.append(line)
        
        # Check if we're entering the target method
        if '.method public isHansFeatureEnable()Z' in line:
            in_target_method = True
            method_indent = line[:len(line) - len(line.lstrip())]
            print(f"  Found method: isHansFeatureEnable")
            i += 1
            continue
        
        # Check if we've left the method
        if in_target_method and '.end method' in line:
            in_target_method = False
            i += 1
            continue
        
        # If we're in the method, look for the patterns
        if in_target_method:
            # Pattern 1: isChinaMode + move-result (may have blank lines between)
            if 'isChinaMode()Z' in line:
                # Look for move-result in the next few lines
                found_move_result = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    if 'move-result' in lines[j]:
                        # Found move-result
                        next_line = lines[j]
                        import re
                        match = re.search(r'move-result v(\d+)', next_line)
                        if match:
                            reg_num = match.group(1)
                            
                            # Add all lines between invoke and move-result
                            for k in range(i + 1, j + 1):
                                new_lines.append(lines[k])
                            
                            # Check if patch already applied
                            patch_exists = False
                            for k in range(j + 1, min(j + 5, len(lines))):
                                if f'const/4 v{reg_num}, 0x0' in lines[k]:
                                    patch_exists = True
                                    break
                            
                            if patch_exists:
                                print(f"  isChinaMode patch already applied, skipping...")
                            else:
                                # Add const/4 vX, 0x0
                                indent = next_line[:len(next_line) - len(next_line.lstrip())]
                                const_line = f"{indent}const/4 v{reg_num}, 0x0\n"
                                new_lines.append("\n")
                                new_lines.append(const_line)
                                print(f"  Added const/4 v{reg_num}, 0x0 after isChinaMode")
                                modified = True
                            
                            i = j + 1
                            found_move_result = True
                            break
                
                if found_move_result:
                    continue
            
            # Pattern 2: isExpRegion + move-result (may have blank lines between)
            elif 'isExpRegion()Z' in line:
                # Look for move-result in the next few lines
                found_move_result = False
                for j in range(i + 1, min(i + 5, len(lines))):
                    if 'move-result' in lines[j]:
                        # Found move-result
                        next_line = lines[j]
                        import re
                        match = re.search(r'move-result v(\d+)', next_line)
                        if match:
                            reg_num = match.group(1)
                            
                            # Add all lines between invoke and move-result
                            for k in range(i + 1, j + 1):
                                new_lines.append(lines[k])
                            
                            # Check if patch already applied
                            patch_exists = False
                            for k in range(j + 1, min(j + 5, len(lines))):
                                if f'const/4 v{reg_num}, 0x1' in lines[k]:
                                    patch_exists = True
                                    break
                            
                            if patch_exists:
                                print(f"  isExpRegion patch already applied, skipping...")
                            else:
                                # Add const/4 vX, 0x1
                                indent = next_line[:len(next_line) - len(next_line.lstrip())]
                                const_line = f"{indent}const/4 v{reg_num}, 0x1\n"
                                new_lines.append("\n")
                                new_lines.append(const_line)
                                print(f"  Added const/4 v{reg_num}, 0x1 after isExpRegion")
                                modified = True
                            
                            i = j + 1
                            found_move_result = True
                            break
                
                if found_move_result:
                    continue
        
        i += 1
    
    # Write the modified content back
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] File patched successfully")
    elif modified and dry_run:
        print(f"  [DRY RUN] Would patch this file")
    
    return modified


def patch_is_gms_restricted(file_path, dry_run=False):
    """
    Patch isGmsRestricted method to remove the if-eqz block.
    
    Removes:
        if-eqz v0, :cond_*
        iget-boolean v0, p0, ...->mGmsRestricted:Z
        return v0
        :cond_*
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    in_target_method = False
    skip_mode = False
    skip_until_cond = None
    
    import re
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if we're entering the target method
        if '.method public isGmsRestricted()Z' in line:
            in_target_method = True
            print(f"  Found method: isGmsRestricted")
            new_lines.append(line)
            i += 1
            continue
        
        # Check if we've left the method
        if in_target_method and '.end method' in line:
            in_target_method = False
            new_lines.append(line)
            i += 1
            continue
        
        # If we're in skip mode, skip until we find the cond label
        if skip_mode and skip_until_cond:
            if skip_until_cond in line:
                # Found the cond label, stop skipping
                skip_mode = False
                skip_until_cond = None
                print(f"  Removed if-eqz block with iget-boolean mGmsRestricted")
                modified = True
                # Skip this cond label line too
                i += 1
                continue
            else:
                # Still in skip mode, don't add this line
                i += 1
                continue
        
        # If we're in the method, look for the pattern
        if in_target_method and not skip_mode:
            # Look for: if-eqz v0, :cond_*
            match = re.search(r'if-eqz\s+v\d+,\s+:cond_([0-9a-f]+)', line)
            if match:
                cond_label = match.group(1)
                
                # Check if the next few lines match the pattern
                # Line i+1 should be blank or comment
                # Line i+2 should be iget-boolean ...->mGmsRestricted:Z
                # Line i+3 should be blank
                # Line i+4 should be return v0
                # Line i+5 should be blank
                # Line i+6 should be :cond_X
                
                found_pattern = False
                for j in range(i + 1, min(i + 10, len(lines))):
                    if 'mGmsRestricted:Z' in lines[j]:
                        # This looks like our pattern
                        # Verify by checking if there's a return and cond label ahead
                        has_return = False
                        has_cond = False
                        for k in range(j + 1, min(j + 5, len(lines))):
                            if 'return v' in lines[k]:
                                has_return = True
                            if f':cond_{cond_label}' in lines[k]:
                                has_cond = True
                                break
                        
                        if has_return and has_cond:
                            found_pattern = True
                            break
                
                if found_pattern:
                    # Check if already patched
                    already_patched = True
                    for j in range(i + 1, min(i + 10, len(lines))):
                        if 'mGmsRestricted:Z' in lines[j]:
                            already_patched = False
                            break
                        if '.end method' in lines[j]:
                            break
                    
                    if already_patched:
                        print(f"  Patch already applied, skipping...")
                        new_lines.append(line)
                    else:
                        # Start skip mode
                        skip_mode = True
                        skip_until_cond = f':cond_{cond_label}'
                        # Don't add the current if-eqz line
                    i += 1
                    continue
        
        new_lines.append(line)
        i += 1
    
    # Write the modified content back
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] File patched successfully")
    elif modified and dry_run:
        print(f"  [DRY RUN] Would patch this file")
    
    return modified


def patch_is_china_mode(file_path, dry_run=False):
    """
    Patch methods to return specific boolean values.
    
    Methods patched:
    - isChinaMode()Z -> return false (0x0)
    - isGmsApp(I)Z -> return false (0x0)
    - isGmsEnable()Z -> return true (0x1)
    
    Replaces entire method body with:
        const/4 v0, 0xVALUE
        return v0
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    method_indent = ""
    
    # List of methods to patch: (method_signature, method_name, return_value)
    target_methods = [
        ('.method public isChinaMode()Z', 'isChinaMode', '0x0'),
        ('.method public isGmsApp(I)Z', 'isGmsApp', '0x0'),
        ('.method public isGmsEnable()Z', 'isGmsEnable', '0x1')
    ]
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if we're entering any target method
        method_found = False
        for target_method, method_name, return_value in target_methods:
            if target_method in line:
                method_found = True
                method_start_line = i
                method_indent = line[:len(line) - len(line.lstrip())]
                print(f"  Found method: {method_name}")
                
                # Add the method signature
                new_lines.append(line)
                
                # Skip all content until .end method
                i += 1
                while i < len(lines) and '.end method' not in lines[i]:
                    i += 1
                
                # Check if already patched by looking at original content
                if i > method_start_line + 1:
                    # Check if the method body is already our patch
                    if (method_start_line + 1 < len(lines) and 
                        method_start_line + 2 < len(lines) and
                        lines[method_start_line + 1].strip() == ".registers 2" and
                        method_start_line + 3 < len(lines) and
                        f'const/4 v0, {return_value}' in lines[method_start_line + 3]):
                        print(f"  Patch already applied, skipping...")
                        # Add all the skipped lines back including .end method
                        for j in range(method_start_line + 1, i + 1):
                            new_lines.append(lines[j])
                        i += 1
                        break
                
                # Add the new method body
                new_lines.append(f"{method_indent}    .registers 2\n")
                new_lines.append("\n")
                new_lines.append(f"{method_indent}    const/4 v0, {return_value}\n")
                new_lines.append("\n")
                new_lines.append(f"{method_indent}    return v0\n")
                
                # Add .end method
                if i < len(lines):
                    new_lines.append(lines[i])
                
                print(f"  Replaced method body with: const/4 v0, {return_value} + return v0")
                modified = True
                i += 1
                break
        
        if not method_found:
            new_lines.append(line)
            i += 1
    
    # Write the modified content back
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] File patched successfully")
    elif modified and dry_run:
        print(f"  [DRY RUN] Would patch this file")
    
    return modified


def patch_register_gms_restrict_observer(file_path, dry_run=False):
    """
    Patch registerGmsRestrictObserver method to be empty (only return-void).
    
    Replaces entire method body with:
        .registers 1
        return-void
    
    Returns:
        True if file was modified, False otherwise
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    in_target_method = False
    method_start_line = -1
    method_indent = ""
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if we're entering the target method
        if '.method private registerGmsRestrictObserver()V' in line:
            in_target_method = True
            method_start_line = i
            method_indent = line[:len(line) - len(line.lstrip())]
            print(f"  Found method: registerGmsRestrictObserver")
            
            # Add the method signature
            new_lines.append(line)
            
            # Skip all content until .end method
            i += 1
            while i < len(lines) and '.end method' not in lines[i]:
                i += 1
            
            # Check if already patched (simple check)
            if i > method_start_line + 1:
                # Check if the method body is already our patch
                if (method_start_line + 1 < len(lines) and 
                    method_start_line + 2 < len(lines) and
                    '.registers 1' in lines[method_start_line + 1] and
                    'return-void' in lines[method_start_line + 2]):
                    print(f"  Patch already applied, skipping...")
                    # Add all the skipped lines back
                    for j in range(method_start_line + 1, i + 1):
                        new_lines.append(lines[j])
                    i += 1
                    in_target_method = False
                    continue
            
            # Add the new method body
            new_lines.append(f"{method_indent}    .registers 1\n")
            new_lines.append(f"{method_indent}    return-void\n")
            
            # Add .end method
            if i < len(lines):
                new_lines.append(lines[i])
            
            print(f"  Replaced method body with: .registers 1 + return-void")
            modified = True
            in_target_method = False
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # Write the modified content back
    if modified and not dry_run:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] File patched successfully")
    elif modified and dry_run:
        print(f"  [DRY RUN] Would patch this file")
    
    return modified


def main():
    parser = argparse.ArgumentParser(
        description='Patch smali files to modify isExpVersion behavior',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview changes
  python patch_isExpVersion.py e:\\smali_org --dry-run
  
  # Apply patches
  python patch_isExpVersion.py e:\\smali_org
  
  # Apply patches to specific file
  python patch_isExpVersion.py e:\\smali_org\\com\\android\\server\\am\\OplusAppStartupConfig.smali
        """
    )
    
    parser.add_argument(
        'target',
        help='Target directory or file to patch'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )
    
    args = parser.parse_args()
    
    # Check if target exists
    if not os.path.exists(args.target):
        print(f"Error: Target path does not exist: {args.target}")
        sys.exit(1)
    
    # Determine if target is file or directory
    if os.path.isfile(args.target):
        smali_files = [args.target]
    else:
        print(f"Searching for .smali files in: {args.target}")
        smali_files = find_smali_files(args.target)
        print(f"Found {len(smali_files)} .smali files")
    
    # Process each file
    modified_count = 0
    
    print("\n" + "=" * 80)
    if args.dry_run:
        print("DRY RUN MODE - No files will be modified")
    print("=" * 80 + "\n")
    
    for file_path in smali_files:
        # Get relative path for display
        rel_path = os.path.relpath(file_path, args.target if os.path.isdir(args.target) else os.path.dirname(args.target))
        
        try:
            file_modified = False
            
            # Apply patch 1: isExpVersion
            if patch_file(file_path, dry_run=args.dry_run):
                file_modified = True
            
            # Apply patch 2: isGoogleRestricInfoOn
            if patch_google_restrict_info(file_path, dry_run=args.dry_run):
                file_modified = True
            
            # Apply patch 3: updateGmsRestrict
            if patch_update_gms_restrict(file_path, dry_run=args.dry_run):
                file_modified = True
            
            # Apply patch 4: isHansFeatureEnable
            if patch_hans_feature_enable(file_path, dry_run=args.dry_run):
                file_modified = True
            
            # Apply patch 5: isGmsRestricted
            if patch_is_gms_restricted(file_path, dry_run=args.dry_run):
                file_modified = True
            
            # Apply patch 6: isChinaMode
            if patch_is_china_mode(file_path, dry_run=args.dry_run):
                file_modified = True
            
            # Apply patch 7: registerGmsRestrictObserver (clean version)
            if patch_register_gms_restrict_observer(file_path, dry_run=args.dry_run):
                file_modified = True
            
            if file_modified:
                modified_count += 1
        except Exception as e:
            print(f"  [ERROR] {e}")
 
    if args.dry_run:
        print("\nThis was a DRY RUN. No files were actually modified.")
        print("Run without --dry-run to apply the changes.")
    
    return 0 if modified_count > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
