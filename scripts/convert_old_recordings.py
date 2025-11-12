#!/usr/bin/env python3
"""
Convert old recording files (without separator) to new format (with separator)
Usage: python3 scripts/convert_old_recordings.py <input_file> <output_file>
"""

import sys
import struct
import json
import shutil
from pathlib import Path

def convert_recording(input_file, output_file):
    """
    Convert old format recording to new format by adding separator

    Old format: [metadata_size][metadata_json][packets...]
    New format: [metadata_size][metadata_json][separator][packets...]
    """

    print(f"🔄 Converting recording format...")
    print(f"📁 Input:  {input_file}")
    print(f"📁 Output: {output_file}")

    with open(input_file, 'rb') as infile:
        # Read metadata
        metadata_size = struct.unpack('<I', infile.read(4))[0]
        metadata_bytes = infile.read(metadata_size)
        metadata = json.loads(metadata_bytes.decode('utf-8'))

        print(f"\n📊 Metadata:")
        print(f"   Port: {metadata.get('port', 'unknown')}")
        print(f"   Date: {metadata.get('recording_date', 'unknown')}")

        # Read all remaining data (packets)
        remaining_data = infile.read()

    # Write new format
    with open(output_file, 'wb') as outfile:
        # Write metadata
        outfile.write(struct.pack('<I', metadata_size))
        outfile.write(metadata_bytes)

        # Write separator (this is what was missing!)
        outfile.write(b"---PACKETS---\n")

        # Write all packet data as-is
        outfile.write(remaining_data)

    # Count packets to verify
    packet_count = 0
    with open(output_file, 'rb') as f:
        # Skip metadata
        meta_size = struct.unpack('<I', f.read(4))[0]
        f.read(meta_size)

        # Skip separator
        f.readline()

        # Count packets
        while True:
            ts_bytes = f.read(8)
            if not ts_bytes:
                break
            size_bytes = f.read(4)
            if not size_bytes:
                break
            size = struct.unpack('<I', size_bytes)[0]
            f.read(size)
            packet_count += 1

    output_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"\n✅ Conversion complete!")
    print(f"   Packets: {packet_count}")
    print(f"   File size: {output_size:.2f} MB")

def convert_directory(directory):
    """Convert all old recording files in a directory"""
    directory = Path(directory)

    if not directory.exists():
        print(f"❌ Directory not found: {directory}")
        return

    pattern = "rig_port*.packets"
    files = list(directory.glob(pattern))

    if not files:
        print(f"❌ No recording files found in {directory}")
        return

    print(f"\n🔍 Found {len(files)} recording file(s) to convert\n")

    for i, input_file in enumerate(files, 1):
        # Create backup
        backup_file = input_file.with_suffix('.packets.backup')

        # Create temporary output
        temp_file = input_file.with_suffix('.packets.tmp')

        print(f"\n[{i}/{len(files)}] Processing {input_file.name}")
        print("=" * 60)

        try:
            # Convert
            convert_recording(input_file, temp_file)

            # Backup original
            shutil.copy2(input_file, backup_file)
            print(f"💾 Backup saved: {backup_file.name}")

            # Replace original with converted
            shutil.move(temp_file, input_file)
            print(f"✅ Updated: {input_file.name}")

        except Exception as e:
            print(f"❌ Error converting {input_file.name}: {e}")
            if temp_file.exists():
                temp_file.unlink()

    print(f"\n{'='*60}")
    print(f"✅ Conversion complete! Converted {len(files)} file(s)")
    print(f"📁 Backups saved with .backup extension")

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  # Convert single file")
        print("  python3 scripts/convert_old_recordings.py <input_file> <output_file>")
        print("")
        print("  # Convert all files in directory")
        print("  python3 scripts/convert_old_recordings.py <directory>")
        print("")
        print("Examples:")
        print("  python3 scripts/convert_old_recordings.py recordings/old.packets recordings/new.packets")
        print("  python3 scripts/convert_old_recordings.py recordings/lan_session")
        sys.exit(1)

    if len(sys.argv) == 2:
        # Convert directory
        convert_directory(sys.argv[1])
    else:
        # Convert single file
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        convert_recording(input_file, output_file)

if __name__ == "__main__":
    main()
