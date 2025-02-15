import datetime
import numpy as np
import pandas as pd
import re
import xlrd
from pandas.tseries.api import guess_datetime_format

from IndexColumnConverter import IndexColumnConverter

CATEGORIES = ['Integer', 'Float', 'Percentage', 'Scientific Notation', 'Date',
              'Time', 'Currency', 'Email', 'Other']
K = 4


class SheetCompressor:
    def __init__(self):
        self.row_candidates = []
        self.column_candidates = []
        self.row_lengths = {}
        self.column_lengths = {}

    #Obtain border, fill, bold info about cell; incomplete
    def get_format(self, xf, wb):
        format_array = []

        #Border
        if xf.border.top_line_style:
            format_array.append('Top Border')
        
        if xf.border.bottom_line_style:
            format_array.append('Bottom Border') 

        if xf.border.left_line_style:
            format_array.append('Left Border')
    
        if xf.border.right_line_style:
            format_array.append('Right Border')

        #Fill
        if xf.background.background_colour_index != 65:
            format_array.append('Fill Color')

        #Bold
        if wb.font_list[xf.font_index].bold:
            format_array.append('Font Bold')
        
        return format_array

    #Encode spreadsheet into markdown format
    def encode(self, wb, sheet):
        converter = IndexColumnConverter()
        markdown = pd.DataFrame(columns = ['Address', 'Value', 'Format'])
        for rowindex, i in sheet.iterrows():
            for colindex, j in enumerate(sheet.columns.tolist()):
                new_row = pd.DataFrame([converter.parse_colindex(colindex + 1) + str(rowindex + 1), i[j],
                                        self.get_format(wb.xf_list[wb.sheet_by_index(0).cell(rowindex, colindex).xf_index], wb)]).T
                new_row.columns = markdown.columns
                markdown = pd.concat([markdown, new_row])
        return markdown
    
    #Checks for identical dtypes across row/column
    def get_dtype_row(self, sheet):
        current_type = []
        for i, j in sheet.iterrows():
            if current_type != (temp := j.apply(type).to_list()):
                current_type = temp
                self.row_candidates.append(i)
    
    def get_dtype_column(self, sheet):
        current_type = []
        for i, j in enumerate(sheet.columns):
            if current_type != (temp := sheet[j].apply(type).to_list()):
                current_type = temp
                self.column_candidates.append(i)
    
    #Checks for length of text across row/column, looks for outliers, marks as candidates
    def get_length_row(self, sheet):
        for i, j in sheet.iterrows():
            self.row_lengths[i] = sum(j.apply(lambda x: 0 if isinstance(x, float) or isinstance(x, int)
                                              or isinstance(x, datetime.datetime) else len(x)))
        mean = np.mean(list(self.row_lengths.values()))
        std = np.std(list(self.row_lengths.values()))
        min = np.max(mean - 2 * std, 0)
        max = mean + 2 * std
        self.row_lengths = dict((k, v) for k, v in self.row_lengths.items() if v < min or v > max)

    def get_length_column(self, sheet):
        for i, j in enumerate(sheet.columns):
            self.column_lengths[i] = sum(sheet[j].apply(lambda x: 0 if isinstance(x, float) or isinstance(x, int)
                                                        or isinstance(x, datetime.datetime) else len(x)))
        mean = np.mean(list(self.column_lengths.values()))
        std = np.std(list(self.column_lengths.values()))
        min = np.max(mean - 2 * std, 0)
        max = mean + 2 * std
        self.column_lengths = dict((k, v) for k, v in self.column_lengths.items() if v < min or v > max)

    def anchor(self, sheet):
        
        #Given num, obtain all integers from num - k to num + k inclusive
        def surrounding_k(num, k):
            return list(range(num - k, num + k + 1))
        
        self.get_dtype_row(sheet)
        self.get_dtype_column(sheet)
        self.get_length_row(sheet)
        self.get_length_column(sheet)

        #Keep candidates found in both dtype/length method
        self.row_candidates = np.intersect1d(list(self.row_lengths.keys()), self.row_candidates)
        self.column_candidates = np.intersect1d(list(self.column_lengths.keys()), self.column_candidates)

        #Beginning/End are candidates
        self.row_candidates = np.append(self.row_candidates, [0, len(sheet) - 1]).astype('int32')
        self.column_candidates = np.append(self.column_candidates, [0, len(sheet.columns) - 1]).astype('int32')

        #Get K closest rows/columns to each candidate
        self.row_candidates = np.unique(list(np.concatenate([surrounding_k(i, K) for i in self.row_candidates]).flat))
        self.column_candidates = np.unique(list(np.concatenate([surrounding_k(i, K) for i in self.column_candidates]).flat))

        #Truncate negative/out of bounds
        self.row_candidates = self.row_candidates[(self.row_candidates >= 0) & (self.row_candidates < len(sheet))]
        self.column_candidates = self.column_candidates[(self.column_candidates >= 0) & (self.column_candidates < len(sheet.columns))]

        sheet = sheet.iloc[self.row_candidates, self.column_candidates]

        #Remap coordinates
        sheet = sheet.reset_index().drop(columns = 'index')
        sheet.columns = list(range(len(sheet.columns)))

        return sheet
    
    #Converts markdown to value-key pair
    def inverted_index(self, markdown):

        #Takes array of Excel cells and combines adjacent cells
        def combine_cells(array):
            
            # Correct version
            # 2d version of summary ranges from leetcode
            # For each row, run summary ranges to get a 1d array, then run summary ranges for each column 

            # Greedy version
            if len(array) == 1:
                return array[0]
            return array[0] + ':' + array[-1]
        
        dictionary = {}
        for _, i in markdown.iterrows():
            if i['Value'] in dictionary:
                dictionary[i['Value']].append(i['Address'])
            else:
                dictionary[i['Value']] = [i['Address']]
        dictionary = {k: v for k, v in dictionary.items() if not pd.isna(k)}
        dictionary = {k: combine_cells(v) for k, v in dictionary.items()}
        return dictionary
    
    #Key-Value to Value-Key for categories
    def inverted_category(self, markdown):
        dictionary = {}
        for _, i in markdown.iterrows():
                dictionary[i['Value']] = i['Category']
        return dictionary
    
    #Regex to NFS
    def get_category(self, string):
        if pd.isna(string):
            return 'Other'
        if isinstance(string, float):
            return 'Float'
        if isinstance(string, int):
            return 'Integer'
        if isinstance(string, datetime.datetime):
            return 'yyyy/mm/dd'
        if re.match('^(\+|-)?\d+$', string) or re.match('^\d{1,3}(,\d{1,3})*$', string): #Steven Smith
            return 'Integer'
        if re.match('^[-+]?\d*\.?\d*$', string) or re.match('^\d{1,3}(,\d{3})*(\.\d+)?$', string): #Steven Smith/Stack Overflow (https://stackoverflow.com/questions/5917082/regular-expression-to-match-numbers-with-or-without-commas-and-decimals-in-text)
            return 'Float'
        if re.match('^[-+]?\d*\.?\d*%$', string) or re.match('^\d{1,3}(,\d{3})*(\.\d+)?%$', string):
            return 'Percentage'
        if re.match('^[-+]?[$]\d*\.?\d{2}$', string) or re.match('^[-+]?[$]\d{1,3}(,\d{3})*(\.\d{2})?$', string): #Michael Ash
            return 'Currency'
        if re.match('\b-?[1-9](?:\.\d+)?[Ee][-+]?\d+\b', string): #Michael Ash
            return 'Scientific Notation'
        if re.match("^((([!#$%&'*+\-/=?^_`{|}~\w])|([!#$%&'*+\-/=?^_`{|}~\w][!#$%&'*+\-/=?^_`{|}~\.\w]{0,}[!#$%&'*+\-/=?^_`{|}~\w]))[@]\w+([-.]\w+)*\.\w+([-.]\w+)*)$", string): #Dave Black RFC 2821
            return 'Email'
        if datetime_format := guess_datetime_format(string):
            return datetime_format
        return 'Other'
    
    def identical_cell_aggregation(self, sheet, dictionary):

        #Handles nan edge cases
        def replace_nan(sheet):
            if pd.isna(sheet):
                return 'Other'
            else:
                return dictionary[sheet]

        #DFS for checking bounds
        def dfs(r, c, val_type):
            match = replace_nan(sheet.iloc[r, c])
            if visited[r][c] or val_type != match:
                return [r, c, r - 1, c - 1]
            visited[r][c] = True
            bounds = [r, c, r, c]
            for i in [[r - 1, c], [r, c - 1], [r + 1, c], [r, c + 1]]:
                if (i[0] < 0) or (i[1] < 0) or (i[0] >= len(sheet)) or (i[1] >= len(sheet.columns)):
                    continue
                match = replace_nan(sheet.iloc[i[0], i[1]])
                if not visited[i[0]][i[1]] and val_type == match: 
                    new_bounds = dfs(i[0], i[1], val_type)
                    bounds = [min(new_bounds[0], bounds[0]), min(new_bounds[1], bounds[1]), max(new_bounds[2], bounds[2]), max(new_bounds[3], bounds[3])]
            return bounds

        m = len(sheet)
        n = len(sheet.columns)

        visited = [[False] * n for _ in range(m)]
        areas = []

        for r in range(m):
            for c in range(n):
                if not visited[r][c]:
                    val_type = replace_nan(sheet.iloc[r, c])
                    bounds = dfs(r, c, val_type)
                    areas.append([(bounds[0], bounds[1]), (bounds[2], bounds[3]), val_type])
        return areas

  class SpreadsheetLLMWrapper:

    def __init__(self):
        return

    def read_spreadsheet(self, file):
        if file.split('.')[-1] != 'xls':
            return
        try:
            wb = xlrd.open_workbook(file, logfile=open(os.devnull,'w'), formatting_info=True)
            return wb
        except xlrd.biffh.XLRDError:
            return 

    #Takes a file, compresses it
    def compress_spreadsheet(self, wb):
        sheet_compressor = SheetCompressor()
        sheet = pd.read_excel(wb, engine='xlrd')
        sheet = sheet.apply(lambda x: x.str.replace('\n', '<br>') if x.dtype == 'object' else x)

        #Move columns to row 1
        sheet.loc[-1] = sheet.columns
        sheet.index += 1
        sheet.sort_index(inplace=True)
        sheet.columns = list(range(len(sheet.columns)))

        #Structural-anchor-based Extraction
        sheet = sheet_compressor.anchor(sheet)

        #Encoding 
        markdown = sheet_compressor.encode(wb, sheet) #Paper encodes first then anchors; I chose to do this in reverse

        #Data-Format Aggregation
        markdown['Category'] = markdown['Value'].apply(lambda x: sheet_compressor.get_category(x))
        category_dict = sheet_compressor.inverted_category(markdown) 
        try:
            areas = sheet_compressor.identical_cell_aggregation(sheet, category_dict)
        except RecursionError:
            return

        #Inverted-index Translation
        compress_dict = sheet_compressor.inverted_index(markdown)

        return areas, compress_dict

    def llm(self, args, area, table):
        spreadsheet_llm = SpreadsheetLLM(args.model)
        output = ''
        if args.table:
            output += spreadsheet_llm.identify_table(area) + '\n'
        if args.question:
            output += spreadsheet_llm.question_answer(table, args.question)
        return output
        
    def write_areas(self, file, areas):
        string = ''
        converter = IndexColumnConverter()
        for i in areas:
            string += ('(' + i[2] + '|' + converter.parse_colindex(i[0][1] + 1) + str(i[0][0] + 1) + ':' 
                        + converter.parse_colindex(i[1][1] + 1) + str(i[1][0] + 1) + '), ')
        with open(file, 'w+', encoding="utf-8") as f:
            f.writelines(string)

    def write_dict(self, file, dict):
        string = ''
        for key, value in dict.items():
            string += (str(value) + ',' + str(key) + '|')
        with open(file, 'w+', encoding="utf-8") as f:
            f.writelines(string)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--compress', action=argparse.BooleanOptionalAction, default=True, help="compress dataset into txt files; must run for LLM to work")
    parser.add_argument('--directory', type=str, default='VFUSE', help='directory of excel files')
    parser.add_argument('--file', type=str, default='7b5a0a10-e241-4c0d-a896-11c7c9bf2040', help='file to work with')
    parser.add_argument('--model', type=str, choices={'gpt-3.5', 'gpt-4', 'mistral', 'llama-2', 'llama-3', 'phi-3'}, default='gpt-3.5', help='llm to use')
    parser.add_argument('--table', action=argparse.BooleanOptionalAction, default=True, help='Whether or not to identify number of tables')
    parser.add_argument('--question', type=str, help='question to ask llm')
    args = parser.parse_args()

    wrapper = SpreadsheetLLMWrapper()
    
    if args.compress:
        for root, dirs, files in os.walk(args.directory):
            for file in files:
                if not (wb := wrapper.read_spreadsheet(os.path.join(root, file))):
                    continue
                try:
                    areas, compress_dict = wrapper.compress_spreadsheet(wb)
                except TypeError:
                    continue
                wrapper.write_areas('output/' + file.split('.')[0] + '_areas.txt', areas)
                wrapper.write_dict('output/' + file.split('.')[0] + '_dict.txt', compress_dict)
                original_size += os.path.getsize(os.path.join(root, file))
                new_size += os.path.getsize('output/' + file.split('.')[0] + '_areas.txt')
                new_size += os.path.getsize('output/' + file.split('.')[0] + '_dict.txt')
        print('Compression Ratio: {}'.format(str(original_size / new_size)))   

    with open('output/' + args.file + '_areas.txt') as f:
        area = f.readlines()
    with open('output/' + args.file + '_dict.txt') as f:
        table = f.readlines()
    print(wrapper.llm(args, area, table))
