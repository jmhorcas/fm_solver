import os
import argparse

from flamapy.metamodels.fm_metamodel.models import FeatureModel
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, UVLWriter

from fm_solver.transformations import FMToFMSans, FMSansWriter, FMSansReader
from fm_solver.transformations.refactorings import (
    RefactoringPseudoComplexConstraint,
    RefactoringStrictComplexConstraint,
    RefactoringRequiresConstraint,
    RefactoringExcludesConstraint
)

from fm_solver.operations import FMConfigurationsNumber
from fm_solver.utils import utils, fm_utils, logging_utils, config_utils


def classic_approach(fm: FeatureModel) -> FeatureModel:
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)
    fm = utils.apply_refactoring(fm, RefactoringRequiresConstraint)
    fm = utils.apply_refactoring(fm, RefactoringExcludesConstraint)
    fm = fm_utils.remove_leaf_abstract_features(fm)
    return fm


def main(fm_filepath: str):
    logging_utils.FM_LOGGER.info(f'Input model: {fm_filepath}')
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}')

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading '{fm_filepath}' model...")
    fm = UVLReader(fm_filepath).transform()
    logging_utils.LOGGER.info(f"FM loaded.")
    logging_utils.FM_LOGGER.info(logging_utils.fm_stats(fm))
    
    # Transform the feature model to FMSans
    logging_utils.LOGGER.info(f"Transforming FM to FMSans...")
    fm_sans = FMToFMSans(fm).transform()
    logging_utils.FM_LOGGER.info(logging_utils.fmsans_stats(fm_sans))
    
    FMSansWriter(f'{fm_name}.json', fm_sans).transform()
    fm_sans = FMSansReader(f'{fm_name}.json').transform()
    fm = fm_sans.get_feature_model()

    # Execute an analysis operation
    n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    print(f'#Configurations: {n_configurations}')

    fm = fm_utils.to_unique_features(fm)
    UVLWriter(fm, fm_name + '_refactored.uvl').transform()


def main_fmsans(fmsans_filepath: str):
    fm_name = os.path.basename(fmsans_filepath).split('.')[0]
    
    # Load the feature model
    fm_sans = FMSansReader(fmsans_filepath).transform()
    fm = fm_sans.get_feature_model()

    # Execute an analysis operation
    n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    print(f'#Configurations: {n_configurations}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FM Solver.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL format.')
    input_model.add_argument('-fmsans', dest='fm_sans', type=str, help='Input feature model in FMSans (.json) format.')
    args = parser.parse_args()

    if args.feature_model:
        main(args.feature_model)
    else:
        main_fmsans(args.fm_sans)
