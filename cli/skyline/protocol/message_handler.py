import collections
import logging

from skyline.legacy_analysis.parser import parse_source_code, analyze_code
from skyline.exceptions import AnalysisError

import skyline.protocol_gen.innpv_pb2 as pm

logger = logging.getLogger(__name__)

RequestContext = collections.namedtuple(
    'RequestContext',
    ['address', 'state', 'sequence_number'],
)


class MessageHandler:
    def __init__(
        self,
        connection_manager,
        message_sender,
        analysis_request_manager,
    ):
        self._connection_manager = connection_manager
        self._message_sender = message_sender
        self._analysis_request_manager = analysis_request_manager

    def _handle_initialize_request(self, message, context):
        if context.state.initialized:
            self._message_sender.send_protocol_error(
                pm.ProtocolError.ErrorCode.ALREADY_INITIALIZED_CONNECTION,
                context,
            )
            return
        if message.protocol_version != 1:
            # We only support version 1 of the protocol.
            self._message_sender.send_protocol_error(
                pm.ProtocolError.ErrorCode.UNSUPPORTED_PROTOCOL_VERSION,
                context,
            )
            self._connection_manager.remove_connection(context.address)
            return

        context.state.initialized = True
        self._message_sender.send_initialize_response(context)

    def _handle_analysis_request(self, message, context):
        if not context.state.initialized:
            self._message_sender.send_protocol_error(
                pm.ProtocolError.ErrorCode.UNINITIALIZED_CONNECTION,
                context,
            )
            return

        self._analysis_request_manager.submit_request(message, context)

    def handle_message(self, raw_data, address):
        try:
            message = pm.FromClient()
            message.ParseFromString(raw_data)
            logger.debug('Received message from (%s:%d).', *address)

            state = self._connection_manager.get_connection_state(address)
            if not state.is_request_current(message):
                logger.debug('Ignoring stale message from (%s:%d).', *address)
                return
            state.update_sequence(message)

            message_type = message.WhichOneof('payload')
            if message_type is None:
                logger.warn('Received empty message from (%s:%d).', *address)
                return

            context = RequestContext(
                state=state,
                address=address,
                sequence_number=message.sequence_number,
            )

            if message_type == 'initialize':
                self._handle_initialize_request(
                    getattr(message, message_type), context)
            elif message_type == 'analysis':
                self._handle_analysis_request(
                    getattr(message, message_type), context)
            else:
                # If the protobuf was compiled properly, this block should
                # never be reached.
                raise AssertionError(
                    'Invalid message type "{}".'.format(message_type))
        except:
            logger.exception(
                'Processing message from (%s:%d) resulted in an exception.',
                *address,
            )