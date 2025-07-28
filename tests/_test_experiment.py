from pathlib import Path
import tempfile

from jules_pytk.experiment import JulesExperiment


def test_new(jules_config_loaded):
    with tempfile.TemporaryDirectory() as temp_dir:
        experiment_dir = Path(temp_dir) / "experiment"

        experiment = JulesExperiment.new(jules_config_loaded, experiment_dir)

        assert experiment_dir.exists()
        assert (experiment_dir / experiment.config.namelists_subdir).exists()
        assert all([file.exists() for file in experiment.input_files])
