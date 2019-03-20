from .. import ReadTimeSeries as ReadTimeSeries_new
from .ReadBatch import ReadBatch

# NOTE: this workflow is for reading samples
# that were saved with text headers generated by SPEC 

class ReadTimeSeries(ReadTimeSeries_new.ReadTimeSeries):

    def __init__(self):
        super(ReadTimeSeries,self).__init__()
        # replace batch reader with legacy version
        self.batch_reader = ReadBatch()
