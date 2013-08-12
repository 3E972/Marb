from ..Global import Color
from .Chart import Chart, ChartStyle

from PySide.QtGui import QPainter, QPen, QColor, QFontMetrics, QPainterPath, QBrush
from PySide.QtCore import QSize, QRect, QPointF, QPoint, Qt


class RadialChart(Chart):
	def __init__(self, parent=None):
		super(RadialChart, self).__init__( parent )
		self._origin = QPointF(20, 20)
		self._centerHoleDiam = 0
		self._nbTicks = 5

	
	def itemPath( self, index ):
		angle = float( self._x / self.model().columnCount() )
		delta = 0.1 * angle
		
		startAngle = angle * index.column()
		startAngle += index.row() * self._x
		
		pathCenter = QPainterPath()
		rectangle = QRect( -self._centerHoleDiam/2, -self._centerHoleDiam/2, self._centerHoleDiam, self._centerHoleDiam )
		rectangle.translate( self._valuesRect.center() )
		
		pathCenter.addEllipse( rectangle )
		y = self.valueToPx( index.data( Qt.DisplayRole ) )
		rectangle = QRect( -y/2, -y/2, y, y )
		rectangle.translate( self._valuesRect.center() )
		path = QPainterPath()
		path.moveTo( self._valuesRect.center() )
		path.arcTo( rectangle, -(startAngle + delta), -(angle - delta * 2) )
		path.closeSubpath();
		path = path.subtracted( pathCenter )
		return path
		
	def _setAlphaBeta(self):
		w = self._valuesRect.width()
		self._centerHoleDiam = w * 0.2
		m = w * 0.3 
		self._alpha = float( w - m ) / float( self._maxBound - self._minBound )
		self._beta = w - self._alpha * self._maxBound


	def _processSpec(self):
		if self.model() == None:
			return None
		
		textWidth = self._scanValues()
		
		self.defineRects()
			
		w = min( self._chartRect.width(), self._chartRect.height() ) - (textWidth + 10 )
		self._valuesRect = QRect( -w/2, -w/2, w, w )
		self._valuesRect.translate( self._chartRect.center().x(), self._chartRect.center().y() )
		
		self._calculateBounds()
		self._x = float( 360.0 ) / ( self.model().rowCount() )
		self._setAlphaBeta()
		
		self._titleRect.moveTo( self._chartRect.bottomLeft() )
		self._titleRect.translate( (self._chartRect.width() - self._titleRect.width())/2, 10 )


	def columnStyle(self, column ):
		'''Returns the style for the column.
		
		If no style has been set for the column, returns the style by default
		'''
		if column in self._style:
			return self._style[ column ]
		else:
			style = ChartStyle()
			c1 = Color.lightColorAt( column )
			c2 = Color.regularColorAt( column )
			c1.setAlpha( 200 )
			style.setPen( QPen( QColor(c2), 2 ) )
			style.setBrush( QBrush(c1) )
			return style

	def paintChart(self, painter):		
		painter.setRenderHints( QPainter.Antialiasing | QPainter.TextAntialiasing )
		
		self._paintText(painter)
		self.__paintTicks( painter )

		cols = self.model().columnCount()
		painter.save()
		for c in range( cols ):
			style = self.columnStyle( c )
			painter.setPen( style.pen() )				
			painter.setBrush( style.brush() )
			self._paintValues( painter, c )
		painter.restore()
			
		self._paintLegend(painter)
		font = self.font()
		font.setItalic( True )
		painter.setFont( font )
		painter.drawText( self._titleRect, Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap, self._title )

		
	def __paintTicks(self, painter):
			y = self._minBound
			painter.save()
			c = QColor(Qt.lightGray)
			c.setAlpha( 100 )
			painter.setPen( QPen( c , 2) )
			
			while y <= self._maxBound:
				v = self.valueToPx( y )
				rectangle = QRect( -v/2, -v/2, v, v )
				rectangle.translate( self._valuesRect.center() )
				path = QPainterPath()
				path.addEllipse( rectangle )
				painter.drawPath( path )
				y += self._tickSize
			
			painter.restore()


	def _paintText(self, painter):
		painter.save()
		metrics = QFontMetrics( self.font() )
		h = metrics.height()
		
		pathCenter = QPainterPath()
		rectangle = QRect( -self._centerHoleDiam/2, -self._centerHoleDiam/2, self._centerHoleDiam, self._centerHoleDiam )
		rectangle.translate( self._valuesRect.center() )		
		pathCenter.addEllipse( rectangle )
		
		c = QColor(Color.LightGray)
		c.setAlpha(100)
		
		penLine = QPen( QColor(c), 2)
		penText = QPen( Qt.gray)
		
		path = QPainterPath()
		rectangle = QRect( self._valuesRect.x(), self._valuesRect.y(), self._valuesRect.width() + 10, self._valuesRect.height() + 10 )
		rectangle.translate( -5, -5)
		path.addEllipse( rectangle )
		
		rows = float(self.model().rowCount())
		r = 0.0
		while ( r < rows ):
			s = str(self.model().headerData( r, Qt.Vertical ))
			p1 = path.pointAtPercent( r / rows )
			p2 = pathCenter.pointAtPercent( r / rows )
			p3 = path.pointAtPercent( (r+0.5) / rows )
			painter.setPen( penLine )
			painter.drawLine( p1, p2 )
			w = metrics.width( s )
			if p3.x() < self._valuesRect.center().x():
				p3 = p3 - QPoint( w, 0 )
			if p3.y() > self._valuesRect.center().y():
				p3 = p3 + QPoint( 0, h )
			painter.setPen( penText )
			painter.drawText( p3, s )
			
			r += 1
			
		painter.restore()
	
	
	def _paintValues( self, painter, column ):
		rows = self.model().rowCount()
		painter.save()
		isActive = False
		selectedIndexes = self.selectionModel().selectedIndexes()
		if selectedIndexes != []:
			for idx in selectedIndexes:
				if idx.column() == column:
					isActive = True
					break
		else:
			isActive = True
		for r in range(0, rows):
			index = self.model().index( r, column )
			painter.save()
			if len( selectedIndexes ) != 0:
				if index not in selectedIndexes:
					if isActive == False:
						c = QColor(Color.Gray)
						c.setAlpha( 125 )
						pen = painter.pen()
						pen.setColor( c )
						painter.setPen( pen )
						c = QColor(Color.LightGray)
						c.setAlpha( 150 )
						painter.setBrush( QBrush( c ) )
					else:
						pen = painter.pen()
						c = pen.color()
						c.setAlpha( c.alpha() * 0.5 )
						pen.setColor( c )
						painter.setPen( pen )
						brush = painter.brush()
						c = brush.color()
						c.setAlpha( c.alpha() * 0.5 )
						brush.setColor( c )
						painter.setBrush( brush )
			path = self.itemPath( index )
			painter.drawPath( path )
			painter.restore()
		painter.restore()


	def _paintColumnLegend(self, painter, c, pos, metricsH):
		r = QRect( pos.x() + 25, pos.y() - 15, 30, 30 )
		posText = pos + QPoint( 45, metricsH/2 )
		
		style = self.columnStyle(c)
		
		s = str(self.model().headerData( c, Qt.Horizontal ))
		painter.drawText( posText, s )
		painter.save()
		painter.setPen( style.pen() )
		painter.setBrush( style.brush() )
		painter.drawPie( r, 210 * 16, -60 * 16 )
		painter.restore()