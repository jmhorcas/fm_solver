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
from fm_solver.utils import utils, fm_utils, logging_utils, timer, sizer
from fm_solver.models import fm_sans as fm_sans_utils

def classic_approach(fm: FeatureModel) -> FeatureModel:
    fm = utils.apply_refactoring(fm, RefactoringPseudoComplexConstraint)
    fm = utils.apply_refactoring(fm, RefactoringStrictComplexConstraint)
    fm = utils.apply_refactoring(fm, RefactoringRequiresConstraint)
    fm = utils.apply_refactoring(fm, RefactoringExcludesConstraint)
    fm = fm_utils.remove_leaf_abstract_features(fm)
    return fm


def main(fm_filepath: str):
    # Get feature model name
    logging_utils.FM_LOGGER.info(f'Input model: {fm_filepath}')
    fm_name = '.'.join(os.path.basename(fm_filepath).split('.')[:-1])
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}')

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading FM '{fm_filepath}' model...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM loading."):
        fm = UVLReader(fm_filepath).transform()
    sizer.getsizeof(fm, logging_utils.LOGGER.info, message="FM.")
    logging_utils.FM_LOGGER.info(fm_sans_utils.fm_stats(fm))
    
    # Transform the feature model to FMSans
    logging_utils.LOGGER.info(f"Transforming FM to FMSans...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM to FMSans transformation."):
        fm_sans = FMToFMSans(fm).transform()
    sizer.getsizeof(fm_sans, logging_utils.LOGGER.info, message="FMSans.")
    logging_utils.FM_LOGGER.info(fm_sans_utils.fmsans_stats(fm_sans))
    
    logging_utils.LOGGER.info(f"Serializing FMSans...")
    output_fmsans_filepath = f'{fm_name}.json'
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FMSans serialization."):
        FMSansWriter(output_fmsans_filepath, fm_sans).transform()
    logging_utils.LOGGER.info(f"FMSans saved at {output_fmsans_filepath}.")

    # ############################################################################
    # fm_sans = FMSansReader(f'{fm_name}.json').transform()
    # fm = fm_sans.get_feature_model()

    # # Execute an analysis operation
    # n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    # print(f'#Configurations: {n_configurations}')

    # UVLWriter(fm, fm_name + '_refactored.uvl').transform()
    # fm = fm_utils.to_unique_features(fm)
    # UVLWriter(fm, fm_name + '_refactored_unique.uvl').transform()


def main_fmsans(fmsans_filepath: str):
    # Get feature model name
    logging_utils.FM_LOGGER.info(f'Input model: {fmsans_filepath}')
    fm_name = os.path.basename(fmsans_filepath).split('.')[0]
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}')

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading FM '{fmsans_filepath}' model...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM loading."):
        fm_sans = FMSansReader(fmsans_filepath).transform()
    sizer.getsizeof(fm_sans, logging_utils.LOGGER.info, message="FMSans.")
    logging_utils.FM_LOGGER.info(fm_sans_utils.fmsans_stats(fm_sans))

    # Get complete feature model
    logging_utils.LOGGER.info(f"Applying IDs transformations...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="Applying IDs transformations."):
        fm = fm_sans.get_feature_model()
        sizer.getsizeof(fm, logging_utils.LOGGER.info, message="FM.")
    logging_utils.FM_LOGGER.info(fm_sans_utils.fm_stats(fm))

    # Execute an analysis operation
    n_configurations = FMConfigurationsNumber().execute(fm).get_result()
    print(f'#Configurations: {n_configurations}')

    logging_utils.LOGGER.info(f"Serializing full FM...")
    output_fm_filepath = f'{fm_name}_refactored.uvl'
    with timer.Timer(logger=logging_utils.LOGGER.info, message="Full FM serialization."):
        UVLWriter(fm, output_fm_filepath).transform()
    logging_utils.LOGGER.info(f"Full FM saved at {output_fm_filepath}.")


def main_fmsans_analysis(fmsans_filepath: str):
    # Get feature model name
    logging_utils.FM_LOGGER.info(f'Input model: {fmsans_filepath}')
    fm_name = '.'.join(os.path.basename(fmsans_filepath).split('.')[:-1])
    logging_utils.FM_LOGGER.info(f'FM name: {fm_name}') 

    # Load the feature model
    logging_utils.LOGGER.info(f"Reading FM '{fmsans_filepath}' model...")
    with timer.Timer(logger=logging_utils.LOGGER.info, message="FM loading."):
        fm = UVLReader(fmsans_filepath).transform()
    sizer.getsizeof(fm, logging_utils.LOGGER.info, message="FM.")
    logging_utils.FM_LOGGER.info(fm_sans_utils.fm_stats(fm))

    # Execute an analysis operation
    with timer.Timer(logger=logging_utils.LOGGER.info, message="Operation: ConfigurationsNumber."):
        n_configurations = FMConfigurationsNumber().execute(fm).get_result()
        print(f'#Configurations: {n_configurations}')
    logging_utils.LOGGER.info(f"Operation: ConfigurationsNumber. Result: {n_configurations}.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='FM Solver.')
    input_model = parser.add_mutually_exclusive_group(required=True)
    input_model.add_argument('-fm', '--featuremodel', dest='feature_model', type=str, help='Input feature model in UVL format.')
    input_model.add_argument('-fmsans', dest='fm_sans', type=str, help='Input feature model in FMSans (.json) format.')
    input_model.add_argument('-fmno', dest='fm_no_ctcs', type=str, help='Input feature model without constraints in UVL format.')
    args = parser.parse_args()

    if args.feature_model:
        main(args.feature_model)
    elif args.fm_sans:
        main_fmsans(args.fm_sans)
    elif args.fm_no_ctcs:
        main_fmsans_analysis(args.fm_no_ctcs)
