from fontTools.pens.basePen import BasePen
from .flatten import InputContour, OutputContour
from pyClipper import PolyClipper # XXX this isn't the real thing


"""
General Suggestions:
- Contours should only be sent here if they actually overlap.
  This can be checked easily using contour bounds.
- Only perform operations on closed contours.
- contours must have an on curve point
- some kind of a log
"""


class BooleanOperationManager(object):

    def _performOperation(self, operation, contours, outPen):
        # prep the contours
        inputContours = [InputContour(contour) for contour in contours]
        # XXX temporary
        clipperContours = []
        for contour in inputContours:
            clipperContours.append(dict(coordinates=contour.originalFlat))
        clipper = PolyClipper.alloc().init()
        resultContours = clipper.execute_operation_withOptions_(clipperContours, operation, dict(subjectFillType="noneZero", clipFillType="noneZero"))
        # the temporary Clipper wrapper is very, very slow
        # at converting back to Python structures. do it here
        # so that the profiling of this can be isolated.
        convertedContours = []
        for contour in resultContours:
            contour = [tuple(point) for point in contour]
            convertedContours.append(contour)
        resultContours = convertedContours
        # /XXX
        # convert to output contours
        outputContours = [OutputContour(contour) for contour in resultContours]
        # re-curve entire contour
        for inputContour in inputContours:
            for outputContour in outputContours:
                if outputContour.final:
                    break
                if outputContour.reCurveFromEntireInputContour(inputContour):
                    # the input is expired if a match was made,
                    # so stop passing it to the outputs
                    break
        # re-curve segments
        for inputContour in inputContours:
            # skip contours that were comppletely used in the previous step
            if inputContour.used:
                continue
            # XXX this could be expensive if an input becomes completely used
            # it doesn't stop from being passed to the output
            for outputContour in outputContours:
                outputContour.reCurveFromInputContourSegments(inputContour)
        # curve fit
        for outputContour in outputContours:
            outputContour.reCurveSubSegments(inputContours)
        # output the results
        for outputContour in outputContours:
            outputContour.drawPoints(outPen)
        # XXX return?
        return outputContours

    def union(self, contours, outPen):
        # XXX return?
        return self._performOperation("union", contours, outPen)
