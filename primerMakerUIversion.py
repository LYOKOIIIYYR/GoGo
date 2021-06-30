# -- coding: utf-8 --

import re
from functools import reduce
import random
import os
import time
import webbrowser

from PySide2.QtWidgets import QApplication, QMessageBox, QFileDialog, QComboBox

from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QIcon

import PySide2

os.environ['QT_MAC_WANTS_LAYER'] = '1'
PySide2_dir = os.path.dirname(PySide2.__file__)
plugin_path = os.path.join(PySide2_dir, 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path


class PrimerMaker:
    def __init__(self):
        # initialize ui
        self.ui = QUiLoader().load('primerMaker.ui')
        self.ui.fileReader.setEnabled(False)
        self.ui.targetSeqInput.setEnabled(True)
        self.ui.promoterInput.setEnabled(False)
        self.ui.addPromoter.setEnabled(False)
        self.ui.dropPromoter.setEnabled(False)
        self.ui.clearPromoter.setEnabled(False)

        self.ui.upstream_overhang.setEnabled(False)
        self.ui.downstream_overhang.setEnabled(False)


        # define initial data
        self.donorType = 'pGN1101'
        self.downstream_overhang = 'GTTT'

        self.ifDefaultOrder = 'y'
        self.seq_decode = {'1': 'AGCCAAGCCAGCAC',
                           '2': 'ACAAGCGGCAGCGC',
                           '3': 'GCCTCAGCGCAGCAG',
                           '4': 'ACGGATCATCTGCACAA',
                            5 : ['ggctacGGTCTCt', 'GTTTCAGAGCTAGAAATAGCAAGTT',
                                 'ggctacGGTCTCt{}'.format(self.get_reverse_complement(self.downstream_overhang))]
                           }
        self.promoter_encode = {'m6a': '1',
                                'm6b': '2',
                                'm6c': '3',
                                'm3': '4',
                                'pGN1101': '5',
                                'pGN1102': '6',
                                'pGN1103': '7',
                                'pGN1104': '8',
                                'custom_donor': '9'
                                }
        self.promoter_decode = dict(zip(self.promoter_encode.values(), self.promoter_encode.keys()))
        self.promoter_downstream = {'1': 'GCCG',
                                    '2': 'GTTG',
                                    '3': 'TCAG',
                                    '4': 'GGCA',
                                    '5': 'GCCG',
                                    '6': 'GGCA',
                                    '7': 'TCAG',
                                    '8': 'GGCA'
                                    }
        # bad_self_pair_seq = ['AGGG', 'CCCT', 'TAAA', 'TTTA', 'TTGA', 'TCAA', 'CCCC', 'GGGG', 'CGCC', 'GGCG']
        self.bad_self_pair_seq = ['GTTT', 'GTGT', 'GCGT', 'GTCT', 'TGCT', 'GGCT', 'AGGG', 'CCCT', 'TAAA', 'TTTA',
                                  'TTGA', 'TCAA', 'TCGG', 'GTCA', 'GACA', 'TGCG', 'CTTG', 'CGTG', 'CGAG', 'CCCC',
                                  'GGGG', 'CGCC', 'GGCG', 'GGAC']

        # input choice
        self.input_source = 'n'
        self.ui.fileCheck.stateChanged.connect(self.fileCheckFunction)
        self.ui.tagetseqClear.clicked.connect(self.inputBoxClear)

        # get work path
        self.workPath = os.getcwd()

        # get file path
        self.ui.fileReader.clicked.connect(self.filePathGet)
        self.filePath = ''

        # table actions
        self.ui.promoterInput.setRowCount(0)
        self.ui.addPromoter.clicked.connect(self.tableAdd)
        self.ui.dropPromoter.clicked.connect(self.tableDrop)
        self.ui.clearPromoter.clicked.connect(self.tableClear)

        # donor group actions
        self.ui.donorGroup.buttonClicked.connect(self.donorGroupSelect)
        self.ui.promoterOrderGroup.buttonClicked.connect(self.promoterOrderGroupSelect)

        # run the program
        self.ui.runButton.clicked.connect(self.mainProgram)

        # save result
        self.ui.saveButton.clicked.connect(self.saveMotion)

        # help
        self.ui.helpButton.clicked.connect(self.helpConnect)

    def inputBoxClear(self):
        self.ui.targetSeqInput.clear()
        self.ui.targetSeqInput.repaint()

    def tableAdd(self):
        currentRow = self.ui.promoterInput.currentRow()
        self.ui.promoterInput.insertRow(currentRow + 1)
        promoter_comboBox = QComboBox()
        promoter_comboBox.addItems(['m6a', 'm6b', 'm6c', 'm3'])
        self.ui.promoterInput.setCellWidget(currentRow + 1, 0, promoter_comboBox)
        self.ui.promoterInput.repaint()
        self.ui.promoterInput.repaint()

    def tableDrop(self):
        currentRow = self.ui.promoterInput.currentRow()
        self.ui.promoterInput.removeRow(currentRow)
        self.ui.promoterInput.repaint()
        self.ui.promoterInput.repaint()

    def tableClear(self):
        self.ui.promoterInput.clearContents()
        self.ui.promoterInput.setRowCount(0)

    def donorGroupSelect(self):
        self.donorType = self.ui.donorGroup.checkedButton().text()
        if self.donorType != 'custom_donor':
            self.ui.upstream_overhang.setEnabled(False)
            self.ui.downstream_overhang.setEnabled(False)
        else:
            self.ui.upstream_overhang.setEnabled(True)
            self.ui.downstream_overhang.setEnabled(True)

    def promoterOrderGroupSelect(self):
        choice = self.ui.promoterOrderGroup.checkedButton().text()
        if choice == 'Default':
            self.ifDefaultOrder = 'y'
            self.ui.promoterInput.setEnabled(False)
            self.ui.addPromoter.setEnabled(False)
            self.ui.dropPromoter.setEnabled(False)
            self.ui.clearPromoter.setEnabled(False)
            self.ui.promoterInput.setRowCount(0)
        else:
            self.ifDefaultOrder = 'n'
            self.ui.promoterInput.setEnabled(True)
            self.ui.addPromoter.setEnabled(True)
            self.ui.dropPromoter.setEnabled(True)
            self.ui.clearPromoter.setEnabled(True)
            self.ui.promoterInput.setRowCount(0)

    def fileCheckFunction(self):
        choice = self.ui.fileCheck.isChecked()
        if choice:
            self.ui.fileReader.setEnabled(True)
            self.ui.targetSeqInput.setEnabled(False)
            self.input_source = 'y'
        else:
            self.ui.fileReader.setEnabled(False)
            self.ui.targetSeqInput.setEnabled(True)
            self.input_source = 'n'
            self.filePath = ''
            self.ui.filePathShow.setText(self.filePath)

    def filePathGet(self):
        self.filePath, _ = QFileDialog.getOpenFileName(self.ui, 'select the file with target sequence')
        self.ui.filePathShow.setText(os.path.basename(self.filePath))

    def saveMotion(self):
        file_name = f'primers_{time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())}.tsv'
        fileName, _ = QFileDialog.getSaveFileName(self.ui,
                                                  'Save as ...',
                                                  f'{self.workPath}/{file_name}'
                                                  )

        if fileName == '':
            return
            # fileName = f'{self.workPath}/{file_name}'
        f = open(fileName, 'w')
        result = self.ui.outputwindow.toPlainText()
        result = re.sub(' *\t', '\t', result)
        f.write(result)
        f.close()
        QMessageBox.information(
            self.ui,
            'Note',
            f'the result has been saved in:\n{fileName}\n')


    @staticmethod
    def helpConnect():
        workPath = os.getcwd()
        webbrowser.open(f'file://{workPath}/HelpDocument.html')

    @staticmethod
    def get_candidate_target_seq_from_file(filename):
        f = open(filename, 'r')
        candidate_target_seq = {}
        module_num = 0
        module_name = []
        for line in f:
            module_num += 1
            line = line.replace('\n', '')
            record = line.split('\t')
            # print(record)
            if len(record) == 1:
                candidate_target_seq[module_num] = record
                module_name.append(str(module_num))
            if len(record) == 2:
                candidate_target_seq[module_num] = [record[1]]
                module_name.append(record[0])

        f.close()
        return candidate_target_seq, module_num, module_name

    @staticmethod
    def get_promoter_order(module_num, if_default, donor, promoter_encode, promoter_order_temp):
        default_order = {0: '',
                         1: '1',
                         2: '12',
                         3: '123',
                         4: '1234',
                         5: '11234',
                         6: '112234',
                         7: '1122334',
                         8: '11223344'
                         }

        promoter_order = promoter_encode[donor]
        if if_default == 'y':
            if module_num - 1 <= 8:
                promoter_order += default_order[module_num - 1]
            else:
                for i in range(module_num - 1):
                    promoter_order += default_order[8][i % 8]
            return list(promoter_order)
        else:
            promoter_order += promoter_order_temp
            return list(promoter_order)

    # cut candidate target sequence according to the promoter downstream and get overhang produced sequence
    @staticmethod
    def deal_candidate_target_seq(promoter_order, candidate_target_seq, promoter_downstream, module_num):
        deal_target_seq = {}
        for promoter_position in range(len(promoter_order)):
            module_position = promoter_position + 1
            seq_deal = []
            for target_seq in candidate_target_seq[module_position]:
                if target_seq[0] == promoter_downstream[promoter_order[promoter_position]][-1]:
                    if module_position == module_num:
                        seq_deal.append(promoter_downstream[promoter_order[promoter_position]] + target_seq[1:])
                    else:
                        seq_deal.append(promoter_downstream[promoter_order[promoter_position]] + target_seq[1:])
                else:
                    if module_position == module_num:
                        seq_deal.append(promoter_downstream[promoter_order[promoter_position]] + target_seq)
                    else:
                        seq_deal.append(promoter_downstream[promoter_order[promoter_position]] + target_seq)
            deal_target_seq[module_position] = seq_deal
        return deal_target_seq

    @classmethod
    def hammingDistance(cls, x, y):
        same_counts = 0
        for i in range(len(x)):
            if x[i].upper() == y[i].upper():
                same_counts += 1
        return same_counts

    @classmethod
    def filter_targets(cls, deal_target_seq, module_num, promoter_order, promoter_downstream, bad_self_pair_seq, self):
        filtered_target = {}
        for module_position in deal_target_seq.keys():
            filtered_overhang = {}
            for target in range(len(deal_target_seq[module_position])):
                if re.search('ggtctc', deal_target_seq[module_position][target], re.I):
                    QMessageBox.critical(
                        self.ui,
                        'Error',
                        f'BsaI site was present within the candidate target {deal_target_seq[module_position][target]} of '
                        f'module {module_position}\n'
                        )

                    return
                if module_position != 1 and module_position != module_num:
                    filtered_overhang[target] = []
                    for i in range(len(deal_target_seq[module_position][target])):
                        if i + 4 <= len(deal_target_seq[module_position][target]):
                            overhang = deal_target_seq[module_position][target][i: i + 4]
                            reverse_overhang = cls.get_reverse_complement(overhang)
                            if overhang != reverse_overhang and \
                                    cls.hammingDistance(overhang, self.downstream_overhang) < 3 and \
                                    cls.hammingDistance(reverse_overhang, self.downstream_overhang) < 3 and \
                                    cls.hammingDistance(overhang, promoter_downstream[promoter_order[0]]) < 3 and \
                                    cls.hammingDistance(reverse_overhang,
                                                        promoter_downstream[promoter_order[0]]) < 3 and \
                                    overhang not in bad_self_pair_seq:
                                filtered_overhang[target].append((overhang, i))

            filtered_target[module_position] = filtered_overhang
        return filtered_target

    @classmethod
    def target_combination(cls, filtered_target):
        filtered_target_list = [x for x in filtered_target.values()]

        # print(type(filtered_target_list))
        def myfunc(list1, list2):
            res = []
            for i in list1:
                # res = []
                if type(i) == tuple:
                    for j in list2:
                        if cls.hammingDistance(i[0], j[0]) < 3 and cls.hammingDistance(cls.get_reverse_complement(i[0]),
                                                                                       j[0]) < 3:
                            res.append([i, j])
                else:
                    for j in list2:
                        condition = 0
                        for k in i:
                            if cls.hammingDistance(k[0], j[0]) >= 3 or cls.hammingDistance(
                                    cls.get_reverse_complement(k[0]),
                                    j[0]) >= 3:
                                condition += 1
                            else:
                                continue
                            # if condition == False:
                            #     break
                        if condition == 0:
                            temp = [x for x in i]
                            temp.append(j)
                            res.append(temp)
                        else:
                            continue
            return random.sample(res, 10)
            # return [i + sep + j for i in list1 for j in list2]

        target_combo = reduce(myfunc, filtered_target_list)
        return target_combo

    # TODO the case of multi targets for each module is not concerned

    @classmethod
    def get_suitable_targets(cls, target_combo):
        suitable_targets = []
        conflict = []
        for targets in target_combo:
            is_suitable = True
            target_list = targets.split(',')
            for i in range(len(target_list)):
                for j in range(i + 1, len(target_list)):
                    if cls.hammingDistance(target_list[i][0:4], target_list[j][0:4]) < 3:
                        is_suitable = True
                    else:
                        is_suitable = False
                        record = (i, j)
                        conflict.append(record)
                    if not is_suitable:
                        break
                if not is_suitable:
                    break
            if is_suitable:
                suitable_targets.append(targets)
        return suitable_targets, conflict

    @classmethod
    def get_reverse_complement(cls, sequence):
        sequence = list(sequence.upper())
        sequence.reverse()
        temp = []
        for i in sequence:
            if i == 'A':
                temp.append('T')
            elif i == 'T':
                temp.append('A')
            elif i == 'C':
                temp.append('G')
            elif i == 'G':
                temp.append('C')
        sequence = ''.join(temp)
        return sequence

    @classmethod
    def primerMakerForOneTarget(cls, target_combo, promoter_order, seq_decode, deal_target_seq):
        primer_list = []
        for filtered_overhang in target_combo:
            primers = []
            for promoter_position in range(len(promoter_order)):
                module_position = promoter_position + 1
                overhang_position = module_position - 2
                if module_position == 1:
                    upstream = seq_decode[5][0] + deal_target_seq[module_position][0] + seq_decode[5][1]
                    downstream = seq_decode[5][0] + cls.get_reverse_complement(
                        deal_target_seq[module_position + 1][0][:filtered_overhang[overhang_position + 1][1] + 4]) + \
                                 seq_decode[promoter_order[module_position]]
                    primer_pair = [upstream, downstream]
                    primers.append(primer_pair)
                elif 1 < module_position < len(promoter_order) - 1:
                    upstream = seq_decode[5][0] + deal_target_seq[module_position][0][
                                                  filtered_overhang[overhang_position][1]:] + seq_decode[5][1]
                    downstream = seq_decode[5][0] + cls.get_reverse_complement(
                        deal_target_seq[module_position + 1][0][:filtered_overhang[overhang_position + 1][1] + 4]) + \
                                 seq_decode[promoter_order[module_position]]
                    primer_pair = [upstream, downstream]
                    primers.append(primer_pair)
                elif module_position == len(promoter_order) - 1:
                    upstream = seq_decode[5][0] + deal_target_seq[module_position][0][
                                                  filtered_overhang[overhang_position][1]:] + seq_decode[5][1]
                    downstream = seq_decode[5][2] + cls.get_reverse_complement(
                        deal_target_seq[module_position + 1][0]) + \
                                 seq_decode[promoter_order[module_position]]
                    primer_pair = [upstream, downstream]
                    primers.append(primer_pair)
            primer_list.append(primers)
        return primer_list

    @staticmethod
    def is_DNA_seq(seq):
        define = []
        DNA_seq = ['A', 'T', 'C', 'G']
        for bp in seq:
            if bp in DNA_seq:
                define.append(True)
            else:
                define.append(False)
        return all(define)


    def mainProgram(self):
        self.ui.outputwindow.clear()
        self.ui.outputwindow.repaint()
        ############################
        # Confirm the custom donor #
        ############################
        if self.donorType == 'custom_donor':
            upstream_overhang = self.ui.upstream_overhang.text().upper()
            reverse_upstream_overhang = self.get_reverse_complement(upstream_overhang)
            downstream_overhang = self.ui.downstream_overhang.text().upper()
            if len(downstream_overhang) == 0:
                downstream_overhang = self.downstream_overhang
            if self.is_DNA_seq(upstream_overhang) is False or self.is_DNA_seq(downstream_overhang) is False:
                QMessageBox.critical(
                    self.ui,
                    'Error',
                    'The user-defined donors must be in correct format.(A string of length 4 containing '
                    'only four elements of A,T,C and G)')
                return
            elif len(upstream_overhang) != 4 or len(downstream_overhang) != 4:
                QMessageBox.critical(
                    self.ui,
                    'Error',
                    'The user-defined donors must be in correct format.(A string of length 4 containing '
                    'only four elements of A,T,C and G)')
                return
            elif self.hammingDistance(upstream_overhang, downstream_overhang) >= 3 or \
                 self.hammingDistance(reverse_upstream_overhang, downstream_overhang) >= 3:
                QMessageBox.critical(
                    self.ui,
                    'Error',
                    'The upstream overhang and downstream overhangs of user-defined donors are homologous '
                    'or complementary, causing error-prone assembly.')
                return
            else:
                self.downstream_overhang = downstream_overhang
                self.promoter_downstream[self.promoter_encode[self.donorType]] = upstream_overhang

        #############################################
        # Obtain module order and candidate targets #
        #############################################
        if self.input_source == 'y':
            candidate_target_seq, module_num, module_name = self.get_candidate_target_seq_from_file(self.filePath)
        else:
            input_from_targetSeqInput = self.ui.targetSeqInput.toPlainText()
            candidate_target_seq = {}
            module_num = len(input_from_targetSeqInput.splitlines())
            promoter_num = module_num
            module_name = []
            for i in range(1, promoter_num + 1):
                if len(input_from_targetSeqInput.splitlines()[i - 1].split('\t')) == 1:
                    candidate_target_seq[i] = input_from_targetSeqInput.splitlines()[i - 1].split('\t')
                    module_name.append(str(i))
                if len(input_from_targetSeqInput.splitlines()[i - 1].split('\t')) == 2:
                    candidate_target_seq[i] = [input_from_targetSeqInput.splitlines()[i - 1].split('\t')[1]]
                    module_name.append(input_from_targetSeqInput.splitlines()[i - 1].split('\t')[0])

        promoter_order_temp = ''
        if self.ifDefaultOrder == 'n':
            tableRowNum = self.ui.promoterInput.rowCount()
            if tableRowNum != module_num - 1:
                QMessageBox.critical(
                    self.ui,
                    'Error',
                    f'Please input the correct amount of modules ！\n with your input data should be {module_num - 1}')
                return
            else:
                for i in range(tableRowNum):
                    rowContent = self.ui.promoterInput.cellWidget(i, 0).currentText()
                    promoter_order_temp += self.promoter_encode[rowContent.lower()]
        promoter_order = self.get_promoter_order(module_num, self.ifDefaultOrder, self.donorType, self.promoter_encode,
                                                 promoter_order_temp)

        #########################################################################
        # Output the sequence that user input and the information of the module #
        #########################################################################
        self.ui.outputwindow.append('The candidate target sequence for every module is:')
        for modulePosition in candidate_target_seq.keys():
            self.ui.outputwindow.append(
                'Module\t{}:\t{}'.format(modulePosition, '\t'.join(candidate_target_seq[modulePosition])))
        self.ui.outputwindow.append('\n')

        self.ui.outputwindow.append('The total amount of module is:\t{}\n'.format(module_num))

        self.ui.outputwindow.append('The donor and the promoter order is:')
        promoterOrderDecode = [self.promoter_decode[x] for x in promoter_order]
        self.ui.outputwindow.append('{}\n\n'.format(' ---> '.join(promoterOrderDecode)))

        # self.ui.outputwindow.append(f'{input_from_targetSeqInput}')
        self.ui.outputwindow.repaint()

        #####################################################
        # Determine the target length based on the promoter #
        #####################################################
        deal_target_seq = self.deal_candidate_target_seq(promoter_order, candidate_target_seq, self.promoter_downstream,
                                                         module_num)
        # print(f'deal_target_seq:\n{deal_target_seq}\n')

        filtered_target = self.filter_targets(deal_target_seq, module_num, promoter_order, self.promoter_downstream,
                                              self.bad_self_pair_seq, self)
        # print(f'filtered_target:\n{filtered_target}\n')

        only1target = 0
        for value in deal_target_seq.values():
            if len(value) != 1:
                only1target += 1
        if only1target == 0:
            filtered_overhang = {}
            for module_position in filtered_target.keys():
                if module_position != 1 and module_position != module_num:
                    filtered_overhang[module_position] = filtered_target[module_position][0]
        else:
            QMessageBox.critical(
                self.ui,
                'Error',
                'Only support one target sequence for each module.\n')
            return

        # print(f'filtered_overhang:\n{filtered_overhang}\n')

        # print(f'promoter_order:\n{promoter_order}\n')

        self.ui.outputwindow.append('The program is running, finding the suitable overhang combination.\n\n')

        if module_num == 1:
            ops1 = deal_target_seq[1][0]
            ps1 = ops1[4:]
            primer_list = [ops1, 'AAAC' + self.get_reverse_complement(ps1)]
            primer_name_len_max = len(module_name[0]) + 2 + 10
            self.ui.outputwindow.append(f'PrimerName{" " * (primer_name_len_max - 10)}\t{"Forward":30}\tLength\tPrimerName{" " * (primer_name_len_max - 10)}\t{"Reverse":30}\tLength\n')
            self.ui.outputwindow.append(f'{module_name[0]}_f{" " * (primer_name_len_max - len(module_name[0]) - 2)}\t{primer_list[0]:30}\t{len(primer_list[0])}\t{module_name[0]}_r{" " * (primer_name_len_max - len(module_name[0]) - 2)}\t{primer_list[1]:30}\t{len(primer_list[0])}\n')
            donor_downstream = [self.promoter_downstream[self.promoter_encode[self.donorType]]]
            overhang = donor_downstream + [self.downstream_overhang]
            self.ui.outputwindow.append('Overhangs:\t{}\n\n'.format(','.join(overhang)))
            self.ui.outputwindow.append('Annealed oligonucleotide pair for direct introduction of protospacer without PCR.\n\n')
            self.ui.outputwindow.repaint()

        elif module_num == 2:
            ops1 = deal_target_seq[1][0]
            primer_name_len_max = len(module_name[-1]) + len(module_name[-2]) + 1 + 7 + 10
            upstream = self.seq_decode[5][0] + ops1 + self.seq_decode[5][1]
            downstream = self.seq_decode[5][2] + self.get_reverse_complement(deal_target_seq[2][0]) + \
                         self.seq_decode[promoter_order[1]]
            self.ui.outputwindow.append(f'PrimerName{" " * (primer_name_len_max - 10)}\t{"Forward":65}\tLength\tPrimerName{" " * (primer_name_len_max - 10)}\t{"Reverse":65}\tLength\n')
            self.ui.outputwindow.append(f'{module_name[0]}&{module_name[1]}_{promoterOrderDecode[1]}_f{" " * 10}\t{upstream:65}\t{len(upstream)}\t{module_name[0]}&{module_name[1]}_{promoterOrderDecode[1]}_r{" " * 10}\t{downstream:65}\t{len(downstream)}\n')
            donor_downstream = [self.promoter_downstream[self.promoter_encode[self.donorType]]]
            overhang = donor_downstream + [self.downstream_overhang]
            self.ui.outputwindow.append('Overhangs:\t{}\n\n'.format(','.join(overhang)))
            self.ui.outputwindow.repaint()

        elif module_num == 3:
            target_combo = self.target_combination(filtered_overhang)
            # print(f'target_combo:\n{target_combo}\n')
            target_combo = [[x] for x in target_combo][:5]
            primer_list = self.primerMakerForOneTarget(target_combo, promoter_order, self.seq_decode, deal_target_seq)

            num = 0
            primer_name_len_max = len(module_name[-1]) + len(module_name[-2]) + 1 + 7 + 10
            self.ui.outputwindow.append(f'{"Choice":6}\tPrimerName{" " * (primer_name_len_max - len("PrimerName"))}\t{"Forward":65}\tLength\tPrimerName{" " * (primer_name_len_max - len("PrimerName"))}\t{"Reverse":65}\tLength\n')
            for primers in primer_list:
                num += 1
                # print(type(primers))
                for i in range(len(primers)):
                    if i != len(primers) - 1:
                        primer_name = f'{module_name[i]}_{promoterOrderDecode[i + 1]}'
                        self.ui.outputwindow.append(f'{num:6}\t{primer_name}_f{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][0]:65}\t{len(primers[i][0])}\t{primer_name}_r{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][1]:65}\t{len(primers[i][1])}\n')
                        # self.ui.outputwindow.append('{:6}\t{:6}\t{:65}\t{}\n'.format(num, i + 1, primers[i][0], primers[i][1]))
                    else:
                        primer_name = f'{module_name[i]}&{module_name[i + 1]}_{promoterOrderDecode[i + 1]}'
                        self.ui.outputwindow.append(f'{num:6}\t{primer_name}_f{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][0]:65}\t{len(primers[i][0])}\t{primer_name}_r{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][1]:65}\t{len(primers[i][1])}\n')
                donor_downstream = [self.promoter_downstream[self.promoter_encode[self.donorType]]]
                overhang_info = target_combo[num - 1]
                overhang = donor_downstream + [seq for seq, site in overhang_info] + [self.downstream_overhang]
                self.ui.outputwindow.append('Overhangs:\t{}\n\n'.format(','.join(overhang)))
            # print(f'primer_list:\n{primer_list}\n')


        elif module_num > 3:
            target_combo = self.target_combination(filtered_overhang)
            # print(target_combo)

            target_combo = target_combo[:5]
            primer_list = self.primerMakerForOneTarget(target_combo, promoter_order, self.seq_decode, deal_target_seq)

            num = 0
            primer_name_len_max = len(module_name[-1]) + len(module_name[-2]) + 1 + 7 + 10
            self.ui.outputwindow.append(
                f'{"Choice":6}\tPrimerName{" " * (primer_name_len_max - len("PrimerName"))}\t{"Forward":65}\tLength\tPrimerName{" " * (primer_name_len_max - len("PrimerName"))}\t{"Reverse":65}\tLength\n')
            # self.ui.outputwindow.append(f'{"Choice":6}\t{"Primer":6}\t{"forward":65}\treverse\n')
            for primers in primer_list:
                num += 1
                # print(type(primers))
                for i in range(len(primers)):
                    if i != len(primers) - 1:
                        primer_name = f'{module_name[i]}_{promoterOrderDecode[i + 1]}'
                        self.ui.outputwindow.append(f'{num:6}\t{primer_name}_f{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][0]:65}\t{len(primers[i][0])}\t{primer_name}_r{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][1]:65}\t{len(primers[i][1])}\n')
                        # self.ui.outputwindow.append('{:6}\t{:6}\t{:65}\t{}\n'.format(num, i + 1, primers[i][0], primers[i][1]))
                    else:
                        primer_name = f'{module_name[i]}&{module_name[i + 1]}_{promoterOrderDecode[i + 1]}'
                        self.ui.outputwindow.append(f'{num:6}\t{primer_name}_f{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][0]:65}\t{len(primers[i][0])}\t{primer_name}_r{" " * (primer_name_len_max - len(primer_name) - 2)}\t{primers[i][1]:65}\t{len(primers[i][1])}\n')
                donor_downstream = [self.promoter_downstream[self.promoter_encode[self.donorType]]]
                overhang_info = target_combo[num - 1]
                overhang = donor_downstream + [seq for seq, site in overhang_info] + [self.downstream_overhang]
                self.ui.outputwindow.append('Overhangs:\t{}\n\n'.format(','.join(overhang)))

        self.ui.outputwindow.append(f'The program is finished.\n')
        self.ui.outputwindow.repaint()




def main():
    app = QApplication([])
    app.setWindowIcon(QIcon('5Goligo.png'))
    primerMaker = PrimerMaker()
    primerMaker.ui.show()
    app.exec_()


if __name__ == '__main__':
    main()
