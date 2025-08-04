#!/usr/bin/env python3
"""
Excel to BRD Converter

This script converts Excel data to BRD (Behavior Recorder Document) format
where each column represents a problem and rows represent the different fields.

Excel format:
- Row 1: Field names (Problem Name, situation-input, etc.)
- Column 1: Problem names (sq1, sq2, sq3, etc.)
- Each column after the first represents a complete problem
"""

import pandas as pd
import importlib.util
try:
    import jieba
except ImportError:
    print("jieba not found, installing...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'jieba'])
    import jieba
import xml.etree.ElementTree as ET
from xml.dom import minidom
import uuid
import argparse
import sys
from pathlib import Path


class BRDGenerator:
    def process_csv_language_translation(self, csv_path, output_dir=None):
        """Process a CSV file in the new language translation format and generate BRD files. Last 20% rows go to brd_test/."""
        df = pd.read_csv(csv_path, dtype=str)
        print(f"Loaded CSV file with {len(df)} rows and {len(df.columns)} columns")
        print(f"Column names: {list(df.columns)}")

        # Shuffle the dataframe before splitting
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)

        # Split into train and test (last 20% for test)
        n_rows = len(df)
        n_test = max(1, int(n_rows * 0.2))
        test_df = df.tail(n_test)
        train_df = df.iloc[:n_rows - n_test] if n_rows > n_test else df.iloc[0:0]

        # Output folders
        parent_dir = Path(csv_path).parent
        gen_1step = parent_dir / "brd_generated_1step"
        gen_2step = parent_dir / "brd_generated_2step"
        test_1step = parent_dir / "brd_test_1step"
        test_2step = parent_dir / "brd_test_2step"
        gen_1step.mkdir(exist_ok=True)
        gen_2step.mkdir(exist_ok=True)
        test_1step.mkdir(exist_ok=True)
        test_2step.mkdir(exist_ok=True)

        def write_brd_files(sub_df, out_dir_1step, out_dir_2step, test_mode=False):
            for count, (idx, row) in enumerate(sub_df.iterrows(), 1):
                situation = str(row.get('Situation', '')).strip()
                rel_a = str(row.get('Relationship-A', '')).strip()
                rel_b = str(row.get('Relationship-B', '')).strip()
                formality = str(row.get('Formality', '')).strip()
                title = str(row.get('Title', '')).strip()
                wrong_titles = str(row.get('Wrong Titles', '')).strip()
                completed_sentence = str(row.get('Completed Sentence', '')).strip()

                if completed_sentence:
                    words = list(jieba.cut(completed_sentence))
                else:
                    words = []

                # 1step: do not use formal-checkbox
                # Randomize correct and wrong titles
                import random
                titles_list = [title] if title else []
                wrong_titles_list = [w.strip() for w in wrong_titles.split() if w.strip()] if wrong_titles else []
                all_titles = titles_list + wrong_titles_list
                random.shuffle(all_titles)
                problem_data_1step = {
                    'situation-input': situation,
                    'relationship-a-input': rel_a,
                    'relationship-b-input': rel_b,
                }
                for i, w in enumerate(all_titles):
                    problem_data_1step[f'option-word-{i+1}'] = w
                for i, w in enumerate(words):
                    problem_data_1step[f'person-a-word-{i+1}'] = w

                # 2step: use formal-checkbox
                problem_data_2step = problem_data_1step.copy()
                problem_data_2step['formal-checkbox'] = formality

                if test_mode:
                    problem_name_1step = f"test_{count}_1step"
                    safe_filename_1step = f"test_{count}_1step"
                    problem_name_2step = f"test_{count}_2step"
                    safe_filename_2step = f"test_{count}_2step"
                else:
                    idx_str = str(idx)
                    problem_name_1step = completed_sentence if completed_sentence else f'problem_{idx_str}_1step'
                    safe_filename_1step = f"problem_{idx_str}_1step"
                    problem_name_2step = completed_sentence if completed_sentence else f'problem_{idx_str}_2step'
                    safe_filename_2step = f"problem_{idx_str}_2step"

                # 1step BRD
                print(f"Processing problem: {problem_name_1step}")
                print(f"  Fields: {list(problem_data_1step.keys())}")
                brd_xml_1step = self.generate_brd(problem_data_1step, problem_name_1step)
                output_file_1step = out_dir_1step / f"{safe_filename_1step}.brd"
                xml_content_1step = '<?xml version="1.0" standalone="yes"?>\n'
                xml_content_1step += self.prettify_xml(brd_xml_1step).split('\n', 1)[1]
                with open(output_file_1step, 'w', encoding='utf-8') as f:
                    f.write(xml_content_1step)
                print(f"  Generated: {output_file_1step}")

                # 2step BRD
                print(f"Processing problem: {problem_name_2step}")
                print(f"  Fields: {list(problem_data_2step.keys())}")
                brd_xml_2step = self.generate_brd(problem_data_2step, problem_name_2step)
                output_file_2step = out_dir_2step / f"{safe_filename_2step}.brd"
                xml_content_2step = '<?xml version="1.0" standalone="yes"?>\n'
                xml_content_2step += self.prettify_xml(brd_xml_2step).split('\n', 1)[1]
                with open(output_file_2step, 'w', encoding='utf-8') as f:
                    f.write(xml_content_2step)
                print(f"  Generated: {output_file_2step}")

        # Write train and test BRDs
        write_brd_files(train_df, gen_1step, gen_2step, test_mode=False)
        write_brd_files(test_df, test_1step, test_2step, test_mode=True)

        print(f"\nAll files generated in: {gen_1step} (train 1step), {gen_2step} (train 2step), {test_1step} (test 1step), and {test_2step} (test 2step)")
    def __init__(self):
        self.node_counter = 1
        self.edge_counter = 1
        
    def generate_uuid(self):
        """Generate a UUID for transaction IDs"""
        return str(uuid.uuid4())
    
    def create_matcher(self, matcher_type, value):
        """Create a matcher element"""
        matcher = ET.Element("matcher")
        matcher_type_elem = ET.SubElement(matcher, "matcherType")
        matcher_type_elem.text = matcher_type
        param = ET.SubElement(matcher, "matcherParameter", name="single")
        param.text = value
        return matcher
    
    def create_action_label(self, selection, action, input_value, hint_message, actor="Tutor (unevaluated)"):
        """Create an action label element"""
        action_label = ET.Element("actionLabel")
        action_label.set("preferPathMark", "true")
        action_label.set("minTraversals", "1")
        action_label.set("maxTraversals", "1")
        
        # Add sub-elements
        ET.SubElement(action_label, "studentHintRequest")
        ET.SubElement(action_label, "stepSuccessfulCompletion")
        ET.SubElement(action_label, "stepStudentError")
        
        unique_id = ET.SubElement(action_label, "uniqueID")
        unique_id.text = str(self.edge_counter)
        
        # Message element
        message = ET.SubElement(action_label, "message")
        verb = ET.SubElement(message, "verb")
        verb.text = "NotePropertySet"
        
        properties = ET.SubElement(message, "properties")
        msg_type = ET.SubElement(properties, "MessageType")
        msg_type.text = "InterfaceAction"
        
        trans_id = ET.SubElement(properties, "transaction_id")
        trans_id.text = self.generate_uuid()
        
        selection_elem = ET.SubElement(properties, "Selection")
        selection_value = ET.SubElement(selection_elem, "value")
        selection_value.text = selection
        
        action_elem = ET.SubElement(properties, "Action")
        action_value = ET.SubElement(action_elem, "value")
        action_value.text = action
        
        input_elem = ET.SubElement(properties, "Input")
        input_value_elem = ET.SubElement(input_elem, "value")
        input_value_elem.text = input_value
        
        # Other elements
        ET.SubElement(action_label, "buggyMessage")
        ET.SubElement(action_label, "successMessage")
        
        hint_msg = ET.SubElement(action_label, "hintMessage")
        hint_msg.text = hint_message
        
        ET.SubElement(action_label, "callbackFn")
        
        action_type = ET.SubElement(action_label, "actionType")
        action_type.text = "Correct Action"
        
        old_action_type = ET.SubElement(action_label, "oldActionType")
        old_action_type.text = "Correct Action"
        
        checked_status = ET.SubElement(action_label, "checkedStatus")
        checked_status.text = "Never Checked"
        
        # Matchers
        matchers = ET.SubElement(action_label, "matchers")
        matchers.set("Concatenation", "true")
        
        selection_matcher = ET.SubElement(matchers, "Selection")
        selection_matcher.append(self.create_matcher("ExactMatcher", selection))
        
        action_matcher = ET.SubElement(matchers, "Action")
        action_matcher.append(self.create_matcher("ExactMatcher", action))
        
        input_matcher = ET.SubElement(matchers, "Input")
        input_matcher.append(self.create_matcher("ExactMatcher", input_value))
        
        actor_elem = ET.SubElement(matchers, "Actor")
        actor_elem.set("linkTriggered", "false")
        actor_elem.text = actor
        
        return action_label
    
    def create_node(self, text, x_pos, y_pos):
        """Create a node element"""
        node = ET.Element("node")
        node.set("locked", "false")
        node.set("doneState", "false")
        
        text_elem = ET.SubElement(node, "text")
        text_elem.text = text
        
        unique_id = ET.SubElement(node, "uniqueID")
        unique_id.text = str(self.node_counter)
        
        dimension = ET.SubElement(node, "dimension")
        x = ET.SubElement(dimension, "x")
        x.text = str(x_pos)
        y = ET.SubElement(dimension, "y")
        y.text = str(y_pos)
        
        current_id = self.node_counter
        self.node_counter += 1
        return node, current_id
    
    def create_edge(self, source_id, dest_id, action_label):
        """Create an edge element"""
        edge = ET.Element("edge")
        edge.append(action_label)
        
        pre_checked = ET.SubElement(edge, "preCheckedStatus")
        pre_checked.text = "No-Applicable"
        
        rule = ET.SubElement(edge, "rule")
        rule_text = ET.SubElement(rule, "text")
        rule_text.text = "unnamed"
        indicator = ET.SubElement(rule, "indicator")
        indicator.text = "-1"
        
        source_id_elem = ET.SubElement(edge, "sourceID")
        source_id_elem.text = str(source_id)
        
        dest_id_elem = ET.SubElement(edge, "destID")
        dest_id_elem.text = str(dest_id)
        
        traversal_count = ET.SubElement(edge, "traversalCount")
        traversal_count.text = "0"
        
        self.edge_counter += 1
        return edge
    
    def extract_problem_data(self, df, problem_column):
        """Extract data for a specific problem column"""
        problem_data = {}
        
        for index, row in df.iterrows():
            field_name = row.iloc[0]  # First column contains field names
            if pd.notna(field_name) and field_name.strip():
                field_name = str(field_name).strip()
                # Clean field name - remove %(...)% wrapper if present
                if field_name.startswith('%(') and field_name.endswith(')%'):
                    field_name = field_name[2:-2]
                
                value = row[problem_column]
                if pd.notna(value) and str(value).strip():
                    problem_data[field_name] = str(value).strip()
        
        return problem_data
    
    def generate_brd(self, problem_data, problem_name):
        """Generate BRD XML for a single problem"""
        # Create root element
        root = ET.Element("stateGraph")
        root.set("firstCheckAllStates", "true")
        root.set("caseInsensitive", "true")
        root.set("unordered", "true")
        root.set("lockWidget", "true")
        root.set("hintPolicy", "Use Both Kinds of Bias")
        root.set("version", "4.0")
        root.set("suppressStudentFeedback", "Show All Feedback")
        root.set("highlightRightSelection", "true")
        root.set("confirmDone", "false")
        root.set("startStateNodeName", "%(startStateNodeName)%")
        root.set("tutorType", "Example-tracing Tutor")
        
        # Start node messages
        start_messages = ET.SubElement(root, "startNodeMessages")
        
        # First message
        msg1 = ET.SubElement(start_messages, "message")
        verb1 = ET.SubElement(msg1, "verb")
        verb1.text = "NotePropertySet"
        props1 = ET.SubElement(msg1, "properties")
        msgtype1 = ET.SubElement(props1, "MessageType")
        msgtype1.text = "StartProblem"
        probname = ET.SubElement(props1, "ProblemName")
        probname.text = "empty"  # Use "empty" as in the original template
        
        # Second message
        msg2 = ET.SubElement(start_messages, "message")
        verb2 = ET.SubElement(msg2, "verb")
        verb2.text = "NotePropertySet"
        props2 = ET.SubElement(msg2, "properties")
        msgtype2 = ET.SubElement(props2, "MessageType")
        msgtype2.text = "StartStateEnd"
        
        # Collect person-a-word fields in order
        person_words = []
        for i in range(2, 16):  # Start from 2 since person-a-word-1 comes at the end
            field_name = f"person-a-word-{i}"
            if field_name in problem_data:
                person_words.append((field_name, problem_data[field_name]))
        
        # Calculate steps
        steps = []
        
        # Basic steps
        for field in ['situation-input', 'relationship-a-input', 'relationship-b-input']:
            if field in problem_data:
                steps.append((field, problem_data[field], "UpdateTextField", "Tutor (unevaluated)"))
        
        # Person word steps (excluding person-a-word-1)
        for field_name, value in person_words:
            steps.append((field_name, value, "UpdateTextField", "Tutor (unevaluated)"))
        
        # Option word steps
        for i in range(1, 6):
            field_name = f"option-word-{i}"
            if field_name in problem_data:
                steps.append((field_name, problem_data[field_name], "UpdateTextField", "Tutor (unevaluated)"))
        
        # Final 3 steps (always in this order)
        if 'formal-checkbox' in problem_data:
            steps.append(('formal-checkbox', problem_data['formal-checkbox'], "UpdateTextField", "Student"))
        
        if 'person-a-word-1' in problem_data:
            steps.append(('person-a-word-1', problem_data['person-a-word-1'], "UpdateTextField", "Student"))
        
        # Done button (always last)
        steps.append(('done', '-1', "ButtonPressed", "Student"))
        
        # Create nodes
        nodes = []
        x_positions = [217, -83]
        y_pos = 25
        y_increment = 160
        
        # First node (empty)
        node, node_id = self.create_node("empty", x_positions[0], y_pos)
        nodes.append((node, node_id))
        root.append(node)
        y_pos += y_increment
        
        # Create nodes for each step
        for i, (field, value, action, actor) in enumerate(steps):
            x_pos = x_positions[(i + 1) % 2]
            node_text = f"state{i + 2}"
            
            node, node_id = self.create_node(node_text, x_pos, y_pos)
            nodes.append((node, node_id))
            root.append(node)
            y_pos += y_increment
        
        # Create edges
        for i, (field, value, action, actor) in enumerate(steps):
            if field == 'done':
                hint_message = "Please click the highlighted button."
            else:
                hint_message = f'Please enter "{value}" in the highlighted field.'
            
            action_label = self.create_action_label(field, action, value, hint_message, actor)
            edge = self.create_edge(nodes[i][1], nodes[i + 1][1], action_label)
            root.append(edge)
        
        # Add EdgesGroups
        edges_groups = ET.SubElement(root, "EdgesGroups")
        edges_groups.set("ordered", "false")
        
        return root
    
    def prettify_xml(self, elem):
        """Return a pretty-printed XML string for the Element."""
        rough_string = ET.tostring(elem, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="    ")
    
    def process_excel_file(self, excel_path, output_dir=None):
        """Process Excel, TSV, or CSV file and generate BRD files. Also trims rows/columns with empty first cell."""
        try:
            ext = str(excel_path).lower()
            if ext.endswith('.csv'):
                # Use the new CSV format handler if columns match
                df = pd.read_csv(excel_path, dtype=str)
                expected_cols = {'Situation','Relationship-A','Relationship-B','Formality','Title','Wrong Titles','Completed Sentence'}
                if expected_cols.issubset(set(df.columns)):
                    return self.process_csv_language_translation(excel_path, output_dir)
                print(f"Loaded CSV file with {len(df)} rows and {len(df.columns)} columns")
            elif ext.endswith('.tsv') or ext.endswith('.txt'):
                df = pd.read_csv(excel_path, sep='\t', dtype=str)
                print(f"Loaded TSV file with {len(df)} rows and {len(df.columns)} columns")
            elif ext.endswith('.xlsx') or ext.endswith('.xls'):
                df = pd.read_excel(excel_path, dtype=str)
                print(f"Loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
            else:
                raise ValueError("Unsupported file type. Please provide an Excel (.xlsx, .xls), TSV (.tsv, .txt), or CSV (.csv) file.")

            print(f"Column names: {list(df.columns)}")

            # Drop rows where the first cell is empty or NaN
            first_col = df.columns[0]
            df = df[df[first_col].notna() & (df[first_col].astype(str).str.strip() != '')]

            # Drop columns where the first cell (row 0) is empty or NaN
            cols_to_keep = [df.columns[0]]
            for col in df.columns[1:]:
                first_cell = df[col].iloc[0] if len(df) > 0 else None
                if pd.notna(first_cell) and str(first_cell).strip() != '':
                    cols_to_keep.append(col)
            df = df[cols_to_keep]

            if output_dir is None:
                output_dir = Path(excel_path).parent / "brd_generated"
            else:
                output_dir = Path(output_dir)

            output_dir.mkdir(exist_ok=True)

            # Process each column (except the first which contains field names)
            for col_index in range(1, len(df.columns)):
                self.node_counter = 1
                self.edge_counter = 1

                problem_column = df.columns[col_index]
                problem_name = str(problem_column)

                # Skip columns that are unnamed or look like default pandas names
                if problem_name.startswith('Unnamed:') or problem_name.strip() == '':
                    print(f"Skipping unnamed/empty column: {problem_name}")
                    continue

                print(f"Processing problem: {problem_name}")

                # Extract problem data from this column
                problem_data = self.extract_problem_data(df, problem_column)

                if not problem_data:
                    print(f"  Skipping {problem_name} - no data found")
                    continue

                # Check if this column has meaningful data (not just empty or default values)
                meaningful_data = {k: v for k, v in problem_data.items() 
                                 if v and v.strip() and v != 'nan' and not k.startswith('Unnamed')}

                if len(meaningful_data) < 2:  # Need at least some meaningful fields
                    print(f"  Skipping {problem_name} - insufficient meaningful data")
                    continue

                print(f"  Found {len(meaningful_data)} meaningful fields")
                print(f"  Fields: {list(meaningful_data.keys())}")

                # Generate BRD XML
                brd_xml = self.generate_brd(meaningful_data, problem_name)

                # Save to file
                safe_filename = problem_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
                output_file = output_dir / f"{safe_filename}.brd"

                # Add XML declaration manually
                xml_content = '<?xml version="1.0" standalone="yes"?>\n'
                xml_content += self.prettify_xml(brd_xml).split('\n', 1)[1]

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(xml_content)

                print(f"  Generated: {output_file}")

            print(f"\nAll files generated in: {output_dir}")

        except Exception as e:
            print(f"Error processing file: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='Convert Excel, TSV, or CSV data to BRD format (columns as problems). Rows and columns with empty first cell are ignored. For CSVs in the language translation format, Chinese sentences are split into words using jieba.')
    parser.add_argument('excel_file', help='Path to the Excel (.xlsx, .xls), TSV (.tsv, .txt), or CSV (.csv) file')
    parser.add_argument('-o', '--output', help='Output directory (default: ./brd_generated)')

    args = parser.parse_args()

    if not Path(args.excel_file).exists():
        print(f"Error: Input file '{args.excel_file}' not found")
        sys.exit(1)

    generator = BRDGenerator()
    generator.process_excel_file(args.excel_file, args.output)


if __name__ == "__main__":
    main()